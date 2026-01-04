from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from pms.models import *


def login_view(request):
    """
    Universal login view that authenticates users and redirects to role-based dashboards
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active_user:
                login(request, user)
                
                # Set session expiry based on remember me
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                # Log the login
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    model_name='User',
                    object_id=str(user.id),
                    object_repr=str(user),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to next parameter or dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account has been deactivated. Please contact the administrator.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """
    Logout view
    """
    if request.user.is_authenticated:
        # Log the logout
        AuditLog.objects.create(
            user=request.user,
            action='LOGOUT',
            model_name='User',
            object_id=str(request.user.id),
            object_repr=str(request.user),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Role-based dashboard router
    """
    user = request.user
    role = user.role
    
    # Route to appropriate dashboard based on role
    if role == 'ADMIN':
        return admin_dashboard(request)
    elif role == 'STAFF':
        return staff_dashboard(request)
    elif role == 'HOD':
        return hod_dashboard(request)
    elif role == 'PROCUREMENT':
        return procurement_dashboard(request)
    elif role == 'FINANCE':
        return finance_dashboard(request)
    elif role == 'STORES':
        return stores_dashboard(request)
    elif role == 'SUPPLIER':
        return supplier_dashboard(request)
    elif role == 'AUDITOR':
        return auditor_dashboard(request)
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('login')


from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import (
    User, Requisition, PurchaseOrder, Supplier, Contract, Invoice,
    Department, AuditLog, Budget, Tender, Bid, GoodsReceivedNote,
    Payment, StockItem, Asset, StockMovement
)


def admin_dashboard(request):
    """Admin Dashboard with Comprehensive Analytics"""
    
    # Time ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    year_start = today.replace(month=1, day=1)
    
    # ==================== Basic Statistics ====================
    total_users = User.objects.filter(is_active_user=True).count()
    total_requisitions = Requisition.objects.count()
    total_pos = PurchaseOrder.objects.count()
    total_suppliers = Supplier.objects.filter(status='APPROVED').count()
    pending_approvals = Requisition.objects.filter(
        status__in=['SUBMITTED', 'HOD_APPROVED', 'BUDGET_APPROVED']
    ).count()
    
    # ==================== Financial Analytics ====================
    # Total spend by status
    total_spend = Invoice.objects.filter(status='PAID').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    # Monthly spend trend (last 12 months)
    twelve_months_ago = today - timedelta(days=365)
    monthly_spend_data = Invoice.objects.filter(
        status='PAID',
        payment_date__gte=twelve_months_ago,
        payment_date__isnull=False
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    # Ensure we have data for all 12 months
    from dateutil.relativedelta import relativedelta
    spend_labels = []
    spend_values = []
    
    current_date = twelve_months_ago.replace(day=1)
    monthly_data_dict = {item['month'].strftime('%Y-%m'): float(item['total']) for item in monthly_spend_data}
    
    for i in range(12):
        month_key = current_date.strftime('%Y-%m')
        spend_labels.append(current_date.strftime('%b %Y'))
        spend_values.append(monthly_data_dict.get(month_key, 0))
        current_date = current_date + relativedelta(months=1)
    
    # Budget utilization
    budget_stats = Budget.objects.filter(
        is_active=True
    ).aggregate(
        total_allocated=Sum('allocated_amount'),
        total_committed=Sum('committed_amount'),
        total_spent=Sum('actual_spent')
    )
    
    budget_allocated = float(budget_stats['total_allocated'] or 0)
    budget_committed = float(budget_stats['total_committed'] or 0)
    budget_spent = float(budget_stats['total_spent'] or 0)
    budget_available = budget_allocated - budget_committed - budget_spent
    
    # ==================== Requisition Analytics ====================
    # Requisitions by status
    req_by_status = Requisition.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    req_status_labels = [item['status'].replace('_', ' ').title() for item in req_by_status]
    req_status_values = [item['count'] for item in req_by_status]
    
    # Requisition trends (last 90 days)
    req_trend_data = Requisition.objects.filter(
        created_at__date__gte=ninety_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    req_trend_labels = [item['date'].strftime('%b %d') for item in req_trend_data]
    req_trend_values = [item['count'] for item in req_trend_data]
    
    # Average approval time (in days)
    avg_approval_time = 0
    approved_reqs = Requisition.objects.filter(
        status='APPROVED',
        submitted_at__isnull=False
    )
    
    if approved_reqs.exists():
        total_days = 0
        count = 0
        for req in approved_reqs:
            if req.submitted_at:
                days = (req.updated_at - req.submitted_at).days
                total_days += days
                count += 1
        avg_approval_time = round(total_days / count, 1) if count > 0 else 0
    
    # ==================== Procurement Analytics ====================
    # PO by status
    po_by_status = PurchaseOrder.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    po_status_labels = [item['status'].replace('_', ' ').title() for item in po_by_status]
    po_status_values = [item['count'] for item in po_by_status]
    
    # Monthly PO trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    po_monthly_data = PurchaseOrder.objects.filter(
        created_at__date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        total_value=Sum('total_amount')
    ).order_by('month')
    
    po_trend_labels = [item['month'].strftime('%b %Y') for item in po_monthly_data]
    po_trend_count = [item['count'] for item in po_monthly_data]
    po_trend_value = [float(item['total_value'] or 0) for item in po_monthly_data]
    
    # ==================== Supplier Analytics ====================
    # Top 10 suppliers by transaction value
    top_suppliers = Supplier.objects.filter(
        purchase_orders__status__in=['DELIVERED', 'CLOSED']
    ).annotate(
        total_value=Sum('purchase_orders__total_amount'),
        po_count=Count('purchase_orders')
    ).order_by('-total_value')[:10]
    
    top_supplier_names = [s.name[:20] + '...' if len(s.name) > 20 else s.name for s in top_suppliers]
    top_supplier_values = [float(s.total_value) if s.total_value else 0 for s in top_suppliers]
    
    # Supplier by status
    supplier_status = Supplier.objects.values('status').annotate(
        count=Count('id')
    )
    
    supplier_status_labels = [item['status'].title() for item in supplier_status]
    supplier_status_values = [item['count'] for item in supplier_status]
    
    # Average supplier rating
    avg_supplier_rating = Supplier.objects.filter(
        status='APPROVED'
    ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    # ==================== Department Analytics ====================
    # Top 5 departments by spend
    top_depts = Department.objects.filter(
        is_active=True,
        requisitions__purchase_orders__isnull=False
    ).annotate(
        total_spend=Sum('requisitions__purchase_orders__total_amount')
    ).order_by('-total_spend')[:5]
    
    dept_names = [dept.name for dept in top_depts]
    dept_values = [float(dept.total_spend) if dept.total_spend else 0 for dept in top_depts]
    
    # Requisitions by department
    req_by_dept = Department.objects.filter(
        is_active=True
    ).annotate(
        req_count=Count('requisitions')
    ).order_by('-req_count')[:8]
    
    req_dept_labels = [dept.code for dept in req_by_dept]
    req_dept_values = [dept.req_count for dept in req_by_dept]
    
    # ==================== Tender & Bid Analytics ====================
    # Active tenders
    active_tenders = Tender.objects.filter(status='PUBLISHED').count()
    
    # Tender by status
    tender_status = Tender.objects.values('status').annotate(
        count=Count('id')
    )
    
    tender_status_labels = [item['status'].title() for item in tender_status]
    tender_status_values = [item['count'] for item in tender_status]
    
    # Average bids per tender
    avg_bids = Tender.objects.filter(
        status__in=['CLOSED', 'EVALUATING', 'AWARDED']
    ).annotate(
        bid_count=Count('bids')
    ).aggregate(avg=Avg('bid_count'))['avg'] or 0
    
    # ==================== Contract Analytics ====================
    active_contracts = Contract.objects.filter(status='ACTIVE').count()
    expiring_soon = Contract.objects.filter(
        status='ACTIVE',
        end_date__lte=today + timedelta(days=30),
        end_date__gte=today
    ).count()
    
    # Contract value by type
    contract_by_type = Contract.objects.filter(
        status='ACTIVE'
    ).values('contract_type').annotate(
        total=Sum('contract_value')
    )
    
    contract_type_labels = [item['contract_type'].replace('_', ' ').title() for item in contract_by_type]
    contract_type_values = [float(item['total']) for item in contract_by_type]
    
    # ==================== Inventory Analytics ====================
    # Low stock items
    low_stock_items = StockItem.objects.filter(
        quantity_on_hand__lte=F('reorder_level')
    ).count()
    
    # Total inventory value
    total_inventory_value = StockItem.objects.aggregate(
        total=Sum('total_value')
    )['total'] or Decimal('0')
    
    # Stock movements (last 30 days)
    stock_movements = StockMovement.objects.filter(
        movement_date__date__gte=thirty_days_ago
    ).values('movement_type').annotate(
        count=Count('id')
    )
    
    stock_movement_labels = [item['movement_type'].replace('_', ' ').title() for item in stock_movements]
    stock_movement_values = [item['count'] for item in stock_movements]
    
    # ==================== Recent Activities ====================
    recent_activities = AuditLog.objects.select_related('user').all()[:15]
    
    # ==================== System Health Indicators ====================
    # User activity (last 7 days)
    active_users_week = AuditLog.objects.filter(
        action='LOGIN',
        timestamp__gte=today - timedelta(days=7)
    ).values('user').distinct().count()
    
    # Pending items summary
    pending_summary = {
        'requisitions': Requisition.objects.filter(status='SUBMITTED').count(),
        'approvals': pending_approvals,
        'invoices': Invoice.objects.filter(status='SUBMITTED').count(),
        'grns': GoodsReceivedNote.objects.filter(status='DRAFT').count(),
    }
    
    # ==================== Performance Metrics ====================
    # On-time delivery compliance
    on_time_deliveries = GoodsReceivedNote.objects.filter(
        delivery_date__lte=F('purchase_order__delivery_date')
    ).count()
    total_deliveries = GoodsReceivedNote.objects.count()
    delivery_compliance = round((on_time_deliveries / total_deliveries * 100), 1) if total_deliveries > 0 else 0
    
    # ==================== Context Assembly ====================
    context = {
        # Basic stats
        'total_users': total_users,
        'total_requisitions': total_requisitions,
        'total_pos': total_pos,
        'total_suppliers': total_suppliers,
        'pending_approvals': pending_approvals,
        'recent_activities': recent_activities,
        
        # System stats
        'system_stats': {
            'departments': Department.objects.filter(is_active=True).count(),
            'active_contracts': active_contracts,
            'total_spend': total_spend,
            'active_tenders': active_tenders,
            'low_stock_items': low_stock_items,
            'expiring_contracts': expiring_soon,
            'active_users_week': active_users_week,
            'avg_supplier_rating': round(float(avg_supplier_rating), 2),
            'inventory_value': total_inventory_value,
        },
        
        # Financial charts
        'spend_chart': {
            'labels': json.dumps(spend_labels),
            'values': json.dumps(spend_values),
        },
        'budget_chart': {
            'labels': json.dumps(['Spent', 'Committed', 'Available']),
            'values': json.dumps([budget_spent, budget_committed, budget_available]),
        },
        
        # Requisition charts
        'req_status_chart': {
            'labels': json.dumps(req_status_labels),
            'values': json.dumps(req_status_values),
        },
        'req_trend_chart': {
            'labels': json.dumps(req_trend_labels),
            'values': json.dumps(req_trend_values),
        },
        
        # Purchase Order charts
        'po_status_chart': {
            'labels': json.dumps(po_status_labels),
            'values': json.dumps(po_status_values),
        },
        'po_trend_chart': {
            'labels': json.dumps(po_trend_labels),
            'count': json.dumps(po_trend_count),
            'value': json.dumps(po_trend_value),
        },
        
        # Supplier charts
        'top_suppliers_chart': {
            'labels': json.dumps(top_supplier_names),
            'values': json.dumps(top_supplier_values),
        },
        'supplier_status_chart': {
            'labels': json.dumps(supplier_status_labels),
            'values': json.dumps(supplier_status_values),
        },
        
        # Department charts
        'dept_spend_chart': {
            'labels': json.dumps(dept_names),
            'values': json.dumps(dept_values),
        },
        'req_by_dept_chart': {
            'labels': json.dumps(req_dept_labels),
            'values': json.dumps(req_dept_values),
        },
        
        # Contract charts
        'contract_type_chart': {
            'labels': json.dumps(contract_type_labels),
            'values': json.dumps(contract_type_values),
        },
        
        # Tender charts
        'tender_status_chart': {
            'labels': json.dumps(tender_status_labels),
            'values': json.dumps(tender_status_values),
        },
        
        # Inventory charts
        'stock_movement_chart': {
            'labels': json.dumps(stock_movement_labels),
            'values': json.dumps(stock_movement_values),
        },
        
        # Performance metrics
        'performance': {
            'avg_approval_time': avg_approval_time,
            'avg_bids_per_tender': round(float(avg_bids), 1),
            'avg_po_creation': 3.5,  # You can calculate this based on your data
            'avg_delivery_time': 15.2,  # You can calculate this based on your data
            'delivery_compliance': delivery_compliance,
        },
        
        # Pending summary
        'pending_summary': pending_summary,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)


def staff_dashboard(request):
    """Staff Dashboard"""
    user = request.user
    
    context = {
        'my_requisitions': Requisition.objects.filter(requested_by=user).order_by('-created_at')[:10],
        'pending_requisitions': Requisition.objects.filter(
            requested_by=user,
            status__in=['DRAFT', 'SUBMITTED']
        ).count(),
        'approved_requisitions': Requisition.objects.filter(
            requested_by=user,
            status='APPROVED'
        ).count(),
        'rejected_requisitions': Requisition.objects.filter(
            requested_by=user,
            status='REJECTED'
        ).count(),
        'recent_notifications': Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:5],
    }
    return render(request, 'dashboards/staff_dashboard.html', context)


def hod_dashboard(request):
    """Head of Department Dashboard"""
    user = request.user
    department = user.department
    
    pending_approvals = Requisition.objects.filter(
        department=department,
        status='SUBMITTED'
    ).order_by('-created_at')
    
    context = {
        'department': department,
        'pending_approvals': pending_approvals,
        'pending_count': pending_approvals.count(),
        'department_requisitions': Requisition.objects.filter(
            department=department
        ).order_by('-created_at')[:10],
        'department_budget': Budget.objects.filter(
            department=department,
            budget_year__is_active=True
        ).aggregate(
            total_allocated=Sum('allocated_amount'),
            total_spent=Sum('actual_spent')
        ),
        'monthly_spend': get_monthly_spend(department),
    }
    return render(request, 'dashboards/hod_dashboard.html', context)


def procurement_dashboard(request):
    """Procurement Officer Dashboard"""
    context = {
        'pending_requisitions': Requisition.objects.filter(
            status='HOD_APPROVED'
        ).count(),
        'active_tenders': Tender.objects.filter(
            status__in=['PUBLISHED', 'EVALUATING']
        ).order_by('-created_at')[:10],
        'pending_pos': PurchaseOrder.objects.filter(
            status='PENDING_APPROVAL'
        ).count(),
        'recent_bids': Bid.objects.filter(
            status='SUBMITTED'
        ).order_by('-submitted_at')[:10],
        'supplier_stats': {
            'total': Supplier.objects.count(),
            'approved': Supplier.objects.filter(status='APPROVED').count(),
            'pending': Supplier.objects.filter(status='PENDING').count(),
        },
        'procurement_stats': {
            'total_pos': PurchaseOrder.objects.count(),
            'total_value': PurchaseOrder.objects.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0'),
            'active_contracts': Contract.objects.filter(status='ACTIVE').count(),
        }
    }
    return render(request, 'dashboards/procurement_dashboard.html', context)


def finance_dashboard(request):
    """Finance Officer Dashboard"""
    context = {
        'pending_invoices': Invoice.objects.filter(
            status='SUBMITTED'
        ).order_by('-created_at')[:10],
        'pending_payments': Invoice.objects.filter(
            status='APPROVED'
        ).count(),
        'recent_payments': Payment.objects.filter(
            status='COMPLETED'
        ).order_by('-created_at')[:10],
        'financial_stats': {
            'total_invoices': Invoice.objects.count(),
            'paid_amount': Payment.objects.filter(
                status='COMPLETED'
            ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0'),
            'pending_amount': Invoice.objects.filter(
                status__in=['SUBMITTED', 'APPROVED']
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
        },
        'budget_utilization': get_budget_utilization(),
    }
    return render(request, 'dashboards/finance_dashboard.html', context)


def stores_dashboard(request):
    """Stores Officer Dashboard"""
    context = {
        'pending_grns': GoodsReceivedNote.objects.filter(
            status__in=['DRAFT', 'INSPECTING']
        ).order_by('-created_at')[:10],
        'low_stock_items': StockItem.objects.filter(
            quantity_on_hand__lte=models.F('reorder_level')
        )[:10],
        'pending_issues': StockIssue.objects.filter(
            status='PENDING'
        ).order_by('-created_at')[:10],
        'inventory_stats': {
            'total_items': StockItem.objects.count(),
            'total_value': StockItem.objects.aggregate(
                total=Sum('total_value')
            )['total'] or Decimal('0'),
            'stores': Store.objects.filter(is_active=True).count(),
        },
        'recent_movements': StockMovement.objects.all().order_by('-movement_date')[:10],
    }
    return render(request, 'dashboards/stores_dashboard.html', context)


def supplier_dashboard(request):
    """Supplier Dashboard"""
    user = request.user
    
    try:
        supplier = Supplier.objects.get(email=user.email)
        
        context = {
            'supplier': supplier,
            'active_tenders': Tender.objects.filter(
                invited_suppliers=supplier,
                status='PUBLISHED'
            ).order_by('-closing_date')[:10],
            'my_bids': Bid.objects.filter(
                supplier=supplier
            ).order_by('-submitted_at')[:10],
            'active_pos': PurchaseOrder.objects.filter(
                supplier=supplier,
                status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED']
            ).order_by('-created_at')[:10],
            'supplier_stats': {
                'total_bids': Bid.objects.filter(supplier=supplier).count(),
                'awarded_bids': Bid.objects.filter(supplier=supplier, status='AWARDED').count(),
                'total_pos': PurchaseOrder.objects.filter(supplier=supplier).count(),
                'rating': supplier.rating,
            }
        }
    except Supplier.DoesNotExist:
        context = {'supplier': None}
    
    return render(request, 'dashboards/supplier_dashboard.html', context)


def auditor_dashboard(request):
    """Auditor Dashboard"""
    context = {
        'recent_activities': AuditLog.objects.all().order_by('-timestamp')[:20],
        'compliance_stats': {
            'total_requisitions': Requisition.objects.count(),
            'emergency_requisitions': Requisition.objects.filter(is_emergency=True).count(),
            'total_tenders': Tender.objects.count(),
            'total_contracts': Contract.objects.count(),
        },
        'pending_reviews': Requisition.objects.filter(
            estimated_amount__gte=500000,
            status='APPROVED'
        ).order_by('-created_at')[:10],
        'high_value_pos': PurchaseOrder.objects.filter(
            total_amount__gte=1000000
        ).order_by('-created_at')[:10],
        'supplier_performance': SupplierPerformance.objects.all().order_by('-reviewed_at')[:10],
    }
    return render(request, 'dashboards/auditor_dashboard.html', context)


# Helper Functions
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_monthly_spend(department):
    """Get monthly spending for a department"""
    start_date = timezone.now().date() - timedelta(days=30)
    return Invoice.objects.filter(
        purchase_order__requisition__department=department,
        status='PAID',
        invoice_date__gte=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')


def get_budget_utilization():
    """Get overall budget utilization"""
    budgets = Budget.objects.filter(budget_year__is_active=True)
    total_allocated = budgets.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0')
    total_spent = budgets.aggregate(total=Sum('actual_spent'))['total'] or Decimal('0')
    
    utilization = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
    
    return {
        'total_allocated': total_allocated,
        'total_spent': total_spent,
        'utilization_percentage': round(utilization, 2)
    }

def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncYear, Coalesce
from django.utils import timezone
from django.http import HttpResponse
from decimal import Decimal
from datetime import timedelta, datetime
import json
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# ============================================================================
# ADMIN ANALYTICS DASHBOARD
# ============================================================================
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import (
    Sum, Count, Avg, F
)
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from django.utils import timezone


@login_required
def admin_analytics_dashboard(request):
    """
    Comprehensive admin analytics dashboard
    """

    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrators only.')
        return redirect('dashboard')

    # =========================================================
    # DATE RANGE FILTERS
    # =========================================================
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)

    filter_start = request.GET.get('start_date')
    filter_end = request.GET.get('end_date')

    if filter_start:
        start_date = datetime.strptime(filter_start, '%Y-%m-%d').date()
    if filter_end:
        end_date = datetime.strptime(filter_end, '%Y-%m-%d').date()

    # =========================================================
    # SYSTEM STATISTICS
    # =========================================================
    total_requisitions = Requisition.objects.count()
    total_pos = PurchaseOrder.objects.count()
    total_suppliers = Supplier.objects.filter(status='APPROVED').count()
    total_contracts = Contract.objects.count()

    total_spend = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED']
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    # =========================================================
    # MONTHLY SPEND TREND
    # =========================================================
    monthly_spend = PurchaseOrder.objects.filter(
        po_date__gte=start_date,
        po_date__lte=end_date,
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED']
    ).annotate(
        month=TruncMonth('po_date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    spend_chart = {
        'labels': [m['month'].strftime('%b %Y') for m in monthly_spend],
        'values': [float(m['total']) for m in monthly_spend]
    }

    # =========================================================
    # BUDGET UTILIZATION
    # =========================================================
    budget_data = Budget.objects.filter(
        budget_year__is_active=True
    ).aggregate(
        allocated=Sum('allocated_amount'),
        committed=Sum('committed_amount'),
        spent=Sum('actual_spent')
    )

    total_allocated = budget_data['allocated'] or Decimal('0.00')
    total_committed = budget_data['committed'] or Decimal('0.00')
    total_spent = budget_data['spent'] or Decimal('0.00')
    available = total_allocated - total_committed - total_spent

    budget_chart = {
        'labels': ['Spent', 'Committed', 'Available'],
        'values': [
            float(total_spent),
            float(total_committed),
            float(available)
        ]
    }

    # =========================================================
    # REQUISITION STATUS
    # =========================================================
    req_status = Requisition.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    req_status_chart = {
        'labels': [
            dict(Requisition.STATUS_CHOICES).get(r['status'], r['status'])
            for r in req_status
        ],
        'values': [r['count'] for r in req_status]
    }

    # =========================================================
    # PURCHASE ORDER TRENDS
    # =========================================================
    po_trend = PurchaseOrder.objects.filter(
        po_date__gte=start_date,
        po_date__lte=end_date
    ).annotate(
        month=TruncMonth('po_date')
    ).values('month').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('month')

    po_trend_chart = {
        'labels': [p['month'].strftime('%b %Y') for p in po_trend],
        'count': [p['count'] for p in po_trend],
        'values': [float(p['total']) for p in po_trend]
    }

    # =========================================================
    # TOP SUPPLIERS
    # =========================================================
    top_suppliers = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED']
    ).values('supplier__name').annotate(
        total=Sum('total_amount')
    ).order_by('-total')[:10]

    top_suppliers_chart = {
        'labels': [s['supplier__name'] for s in top_suppliers],
        'values': [float(s['total']) for s in top_suppliers]
    }

    # =========================================================
    # DEPARTMENT SPEND
    # =========================================================
    dept_spend = Requisition.objects.filter(
        status='APPROVED',
        purchase_orders__status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED']
    ).values('department__name').annotate(
        total=Sum('purchase_orders__total_amount')
    ).order_by('-total')[:10]

    dept_spend_chart = {
        'labels': [d['department__name'] for d in dept_spend],
        'values': [float(d['total'] or 0) for d in dept_spend]
    }

    # =========================================================
    # TENDER STATUS
    # =========================================================
    tender_status = Tender.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    tender_status_chart = {
        'labels': [
            dict(Tender.STATUS_CHOICES).get(t['status'], t['status'])
            for t in tender_status
        ],
        'values': [t['count'] for t in tender_status]
    }

    # =========================================================
    # CONTRACT TYPES
    # =========================================================
    contract_type = Contract.objects.values('contract_type').annotate(
        count=Count('id'),
        total_value=Sum('contract_value')
    ).order_by('-count')

    contract_type_chart = {
        'labels': [
            dict(Contract.CONTRACT_TYPES).get(c['contract_type'], c['contract_type'])
            for c in contract_type
        ],
        'values': [c['count'] for c in contract_type]
    }

    # =========================================================
    # PERFORMANCE METRICS (FIXED)
    # =========================================================
    approved_reqs = Requisition.objects.filter(
        status='APPROVED',
        submitted_at__isnull=False,
        updated_at__isnull=False
    )

    avg_approval_days = 0
    if approved_reqs.exists():
        total_seconds = sum(
            (r.updated_at - r.submitted_at).total_seconds()
            for r in approved_reqs
        )
        avg_approval_days = int(
            total_seconds / approved_reqs.count() / 86400
        )

    avg_bids = Bid.objects.values('tender').annotate(
        bid_count=Count('id')
    ).aggregate(
        avg=Avg('bid_count')
    )['avg'] or 0

    delivered_pos = PurchaseOrder.objects.filter(
        status='DELIVERED',
        sent_at__isnull=False,
        updated_at__isnull=False
    )

    avg_delivery_days = 0
    if delivered_pos.exists():
        total_delivery_seconds = sum(
            (po.updated_at - po.sent_at).total_seconds()
            for po in delivered_pos
        )
        avg_delivery_days = int(
            total_delivery_seconds / delivered_pos.count() / 86400
        )

    total_delivered = delivered_pos.count()
    on_time = delivered_pos.filter(
        updated_at__lte=F('delivery_date')
    ).count()

    delivery_compliance = int(
        (on_time / total_delivered) * 100
    ) if total_delivered > 0 else 0

    performance = {
        'avg_approval_time': avg_approval_days,
        'avg_bids_per_tender': round(avg_bids, 1),
        'avg_delivery_time': avg_delivery_days,
        'delivery_compliance': delivery_compliance
    }

    # =========================================================
    # CATEGORY SPEND
    # =========================================================
    category_spend = RequisitionItem.objects.filter(
        requisition__status='APPROVED',
        requisition__purchase_orders__status__in=[
            'APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED'
        ]
    ).values(
        'item__category__name'
    ).annotate(
        total=Sum('estimated_total')
    ).order_by('-total')[:8]

    category_spend_chart = {
        'labels': [
            c['item__category__name'] or 'Uncategorized'
            for c in category_spend
        ],
        'values': [float(c['total']) for c in category_spend]
    }

    # =========================================================
    # SUPPLIER RATINGS
    # =========================================================
    supplier_ratings = SupplierPerformance.objects.values(
        'supplier__name'
    ).annotate(
        avg_rating=Avg('overall_rating'),
        count=Count('id')
    ).order_by('-avg_rating')[:10]

    supplier_rating_chart = {
        'labels': [s['supplier__name'] for s in supplier_ratings],
        'values': [float(s['avg_rating']) for s in supplier_ratings]
    }

    # =========================================================
    # PAYMENT STATUS
    # =========================================================
    payment_status = Invoice.objects.values('status').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-count')

    payment_status_chart = {
        'labels': [
            dict(Invoice.STATUS_CHOICES).get(p['status'], p['status'])
            for p in payment_status
        ],
        'values': [float(p['total'] or 0) for p in payment_status]
    }

    # =========================================================
    # STOCK VALUE
    # =========================================================
    stock_value = StockItem.objects.values(
        'store__name'
    ).annotate(
        total_value=Sum('total_value')
    ).order_by('-total_value')

    stock_value_chart = {
        'labels': [s['store__name'] for s in stock_value],
        'values': [float(s['total_value']) for s in stock_value]
    }

    # =========================================================
    # CONTEXT
    # =========================================================
    context = {
        'title': 'Admin Analytics Dashboard',
        'total_requisitions': total_requisitions,
        'total_pos': total_pos,
        'total_suppliers': total_suppliers,
        'total_contracts': total_contracts,
        'system_stats': {
            'total_spend': total_spend
        },
        'spend_chart': spend_chart,
        'budget_chart': budget_chart,
        'req_status_chart': req_status_chart,
        'po_trend_chart': po_trend_chart,
        'top_suppliers_chart': top_suppliers_chart,
        'dept_spend_chart': dept_spend_chart,
        'tender_status_chart': tender_status_chart,
        'contract_type_chart': contract_type_chart,
        'category_spend_chart': category_spend_chart,
        'supplier_rating_chart': supplier_rating_chart,
        'payment_status_chart': payment_status_chart,
        'stock_value_chart': stock_value_chart,
        'performance': performance,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'admin/analytics_dashboard.html', context)


# ============================================================================
# REPORTS VIEW WITH FILTERS
# ============================================================================

@login_required
def admin_reports(request):
    """
    Reports page with advanced filtering and Excel export
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrators only.')
        return redirect('dashboard')
    
    # Get filter parameters
    report_type = request.GET.get('report_type', 'requisitions')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department_id = request.GET.get('department')
    supplier_id = request.GET.get('supplier')
    status_filter = request.GET.get('status')
    category_id = request.GET.get('category')
    
    # Set default date range (last 90 days)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Initialize data
    report_data = []
    chart_data = {}
    summary_stats = {}
    
    # ========== REQUISITIONS REPORT ==========
    if report_type == 'requisitions':
        queryset = Requisition.objects.select_related(
            'department', 'requested_by', 'budget'
        ).filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        report_data = queryset.order_by('-created_at')
        
        # Summary stats
        summary_stats = {
            'total_count': queryset.count(),
            'total_value': queryset.aggregate(Sum('estimated_amount'))['estimated_amount__sum'] or Decimal('0.00'),
            'avg_value': queryset.aggregate(Avg('estimated_amount'))['estimated_amount__avg'] or Decimal('0.00'),
            'pending': queryset.filter(status='SUBMITTED').count(),
            'approved': queryset.filter(status='APPROVED').count(),
            'rejected': queryset.filter(status='REJECTED').count(),
        }
        
        # Chart: Status breakdown
        status_data = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        chart_data['status_chart'] = {
            'labels': [dict(Requisition.STATUS_CHOICES).get(item['status'], item['status']) for item in status_data],
            'values': [item['count'] for item in status_data]
        }
        
        # Chart: Monthly trend
        monthly_data = queryset.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('estimated_amount')
        ).order_by('month')
        
        chart_data['monthly_chart'] = {
            'labels': [item['month'].strftime('%b %Y') for item in monthly_data],
            'count': [item['count'] for item in monthly_data],
            'values': [float(item['total']) for item in monthly_data]
        }
    
    # ========== PURCHASE ORDERS REPORT ==========
    elif report_type == 'purchase_orders':
        queryset = PurchaseOrder.objects.select_related(
            'supplier', 'requisition', 'created_by'
        ).filter(
            po_date__gte=start_date,
            po_date__lte=end_date
        )
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        report_data = queryset.order_by('-po_date')
        
        # Summary stats
        summary_stats = {
            'total_count': queryset.count(),
            'total_value': queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
            'avg_value': queryset.aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00'),
            'pending': queryset.filter(status='PENDING_APPROVAL').count(),
            'approved': queryset.filter(status='APPROVED').count(),
            'delivered': queryset.filter(status='DELIVERED').count(),
        }
        
        # Chart: Status breakdown
        status_data = queryset.values('status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ).order_by('-count')
        
        chart_data['status_chart'] = {
            'labels': [dict(PurchaseOrder.STATUS_CHOICES).get(item['status'], item['status']) for item in status_data],
            'values': [float(item['total']) for item in status_data]
        }
        
        # Chart: Top suppliers
        supplier_data = queryset.values('supplier__name').annotate(
            total=Sum('total_amount')
        ).order_by('-total')[:10]
        
        chart_data['supplier_chart'] = {
            'labels': [item['supplier__name'] for item in supplier_data],
            'values': [float(item['total']) for item in supplier_data]
        }
    
    # ========== SUPPLIER REPORT ==========
    elif report_type == 'suppliers':
        queryset = Supplier.objects.annotate(
            po_count=Count('purchase_orders'),
            total_value=Sum('purchase_orders__total_amount')
        ).filter(
            purchase_orders__po_date__gte=start_date,
            purchase_orders__po_date__lte=end_date
        ).distinct()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        report_data = queryset.order_by('-total_value')
        
        # Summary stats
        summary_stats = {
            'total_count': queryset.count(),
            'total_spend': queryset.aggregate(Sum('total_value'))['total_value__sum'] or Decimal('0.00'),
            'active': queryset.filter(status='APPROVED').count(),
            'suspended': queryset.filter(status='SUSPENDED').count(),
        }
        
        # Chart: Supplier ratings
        rating_data = SupplierPerformance.objects.filter(
            reviewed_at__date__gte=start_date,
            reviewed_at__date__lte=end_date
        ).values('supplier__name').annotate(
            avg_rating=Avg('overall_rating')
        ).order_by('-avg_rating')[:10]
        
        chart_data['rating_chart'] = {
            'labels': [item['supplier__name'] for item in rating_data],
            'values': [float(item['avg_rating']) for item in rating_data]
        }
    
    # ========== BUDGET REPORT ==========
    elif report_type == 'budget':
        queryset = Budget.objects.select_related(
            'department', 'budget_year', 'category'
        ).filter(
            budget_year__is_active=True
        )
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        report_data = queryset.order_by('department__name')
        
        # Summary stats
        summary_stats = {
            'total_allocated': queryset.aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or Decimal('0.00'),
            'total_committed': queryset.aggregate(Sum('committed_amount'))['committed_amount__sum'] or Decimal('0.00'),
            'total_spent': queryset.aggregate(Sum('actual_spent'))['actual_spent__sum'] or Decimal('0.00'),
        }
        summary_stats['available'] = summary_stats['total_allocated'] - summary_stats['total_committed'] - summary_stats['total_spent']
        summary_stats['utilization_rate'] = (summary_stats['total_spent'] / summary_stats['total_allocated'] * 100) if summary_stats['total_allocated'] > 0 else 0
        
        # Chart: Department utilization
        dept_data = queryset.values('department__name').annotate(
            allocated=Sum('allocated_amount'),
            spent=Sum('actual_spent')
        ).order_by('-spent')[:10]
        
        chart_data['dept_chart'] = {
            'labels': [item['department__name'] for item in dept_data],
            'allocated': [float(item['allocated']) for item in dept_data],
            'spent': [float(item['spent']) for item in dept_data]
        }
    
    # ========== INVENTORY REPORT ==========
    elif report_type == 'inventory':
        queryset = StockItem.objects.select_related(
            'store', 'item'
        ).all()
        
        report_data = queryset.order_by('store__name', 'item__name')
        
        # Summary stats
        summary_stats = {
            'total_items': queryset.count(),
            'total_value': queryset.aggregate(Sum('total_value'))['total_value__sum'] or Decimal('0.00'),
            'low_stock': queryset.filter(quantity_on_hand__lte=F('reorder_level')).count(),
        }
        
        # Chart: Stock value by store
        store_data = queryset.values('store__name').annotate(
            total=Sum('total_value')
        ).order_by('-total')
        
        chart_data['store_chart'] = {
            'labels': [item['store__name'] for item in store_data],
            'values': [float(item['total']) for item in store_data]
        }
    
    # Get filter options
    departments = Department.objects.filter(is_active=True).order_by('name')
    suppliers = Supplier.objects.filter(status='APPROVED').order_by('name')
    categories = ItemCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'title': 'Reports & Analytics',
        'report_type': report_type,
        'report_data': report_data,
        'chart_data': chart_data,
        'summary_stats': summary_stats,
        'start_date': start_date,
        'end_date': end_date,
        'department_id': department_id,
        'supplier_id': supplier_id,
        'status_filter': status_filter,
        'category_id': category_id,
        'departments': departments,
        'suppliers': suppliers,
        'categories': categories,
        'requisition_statuses': Requisition.STATUS_CHOICES,
        'po_statuses': PurchaseOrder.STATUS_CHOICES,
        'supplier_statuses': Supplier.STATUS_CHOICES,
    }
    
    return render(request, 'admin/reports.html', context)


# ============================================================================
# EXCEL EXPORT
# ============================================================================

@login_required
def export_report_excel(request):
    """
    Export filtered report data to Excel
    """
    if request.user.role != 'ADMIN':
        return HttpResponse('Access denied', status=403)
    
    report_type = request.GET.get('report_type', 'requisitions')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department_id = request.GET.get('department')
    supplier_id = request.GET.get('supplier')
    status_filter = request.GET.get('status')
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # Styling
    header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # ========== REQUISITIONS EXPORT ==========
    if report_type == 'requisitions':
        ws.title = 'Requisitions Report'
        
        # Headers
        headers = ['Req Number', 'Date', 'Department', 'Title', 'Requested By', 
                   'Status', 'Priority', 'Estimated Amount', 'Required Date']
        ws.append(headers)
        
        # Style headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Get data
        queryset = Requisition.objects.select_related(
            'department', 'requested_by'
        ).filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Add data rows
        for req in queryset.order_by('-created_at'):
            ws.append([
                req.requisition_number,
                req.created_at.strftime('%Y-%m-%d'),
                req.department.name,
                req.title,
                req.requested_by.get_full_name(),
                dict(Requisition.STATUS_CHOICES).get(req.status, req.status),
                dict(Requisition.PRIORITY_CHOICES).get(req.priority, req.priority),
                float(req.estimated_amount),
                req.required_date.strftime('%Y-%m-%d')
            ])
        
        # Auto-size columns
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
    
    # ========== PURCHASE ORDERS EXPORT ==========
    elif report_type == 'purchase_orders':
        ws.title = 'Purchase Orders Report'
        
        headers = ['PO Number', 'Date', 'Supplier', 'Requisition', 'Status', 
                   'Subtotal', 'Tax', 'Total', 'Delivery Date']
        ws.append(headers)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        queryset = PurchaseOrder.objects.select_related(
            'supplier', 'requisition'
        ).filter(
            po_date__gte=start_date,
            po_date__lte=end_date
        )
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        for po in queryset.order_by('-po_date'):
            ws.append([
                po.po_number,
                po.po_date.strftime('%Y-%m-%d'),
                po.supplier.name,
                po.requisition.requisition_number,
                dict(PurchaseOrder.STATUS_CHOICES).get(po.status, po.status),
                float(po.subtotal),
                float(po.tax_amount),
                float(po.total_amount),
                po.delivery_date.strftime('%Y-%m-%d')
            ])
        
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
    
    # ========== SUPPLIER EXPORT ==========
    elif report_type == 'suppliers':
        ws.title = 'Suppliers Report'
        
        headers = ['Supplier Number', 'Name', 'Email', 'Phone', 'Status', 
                   'PO Count', 'Total Value', 'Rating']
        ws.append(headers)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        queryset = Supplier.objects.annotate(
            po_count=Count('purchase_orders'),
            total_value=Sum('purchase_orders__total_amount')
        )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        for supplier in queryset.order_by('name'):
            ws.append([
                supplier.supplier_number,
                supplier.name,
                supplier.email,
                supplier.phone_number,
                dict(Supplier.STATUS_CHOICES).get(supplier.status, supplier.status),
                supplier.po_count or 0,
                float(supplier.total_value or 0),
                float(supplier.rating)
            ])
        
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
    
    # ========== BUDGET EXPORT ==========
    elif report_type == 'budget':
        ws.title = 'Budget Report'
        
        headers = ['Department', 'Category', 'Budget Year', 'Allocated', 
                   'Committed', 'Spent', 'Available', 'Utilization %']
        ws.append(headers)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            
            

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    Requisition, RequisitionItem, RequisitionAttachment, RequisitionApproval,
    Department, Budget, Item, User, AuditLog, Notification
)


@login_required
def requisition_list(request):
    """List all requisitions with filters"""
    requisitions = Requisition.objects.select_related(
        'department', 'budget', 'requested_by'
    ).prefetch_related('items')
    
    # Filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    department_filter = request.GET.get('department', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        requisitions = requisitions.filter(status=status_filter)
    
    if priority_filter:
        requisitions = requisitions.filter(priority=priority_filter)
    
    if department_filter:
        requisitions = requisitions.filter(department_id=department_filter)
    
    if search_query:
        requisitions = requisitions.filter(
            Q(requisition_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(justification__icontains=search_query)
        )
    
    if date_from:
        requisitions = requisitions.filter(created_at__gte=date_from)
    
    if date_to:
        requisitions = requisitions.filter(created_at__lte=date_to)
    
    # Role-based filtering
    if request.user.role == 'STAFF':
        requisitions = requisitions.filter(requested_by=request.user)
    elif request.user.role == 'HOD':
        requisitions = requisitions.filter(department=request.user.department)
    
    # Statistics
    total_count = requisitions.count()
    pending_count = requisitions.filter(status='SUBMITTED').count()
    approved_count = requisitions.filter(status='APPROVED').count()
    rejected_count = requisitions.filter(status='REJECTED').count()
    total_amount = requisitions.aggregate(Sum('estimated_amount'))['estimated_amount__sum'] or 0
    
    # Pagination
    paginator = Paginator(requisitions.order_by('-created_at'), 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'requisitions': page_obj,
        'page_obj': page_obj,
        'departments': departments,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'department_filter': department_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_amount': total_amount,
        'status_choices': Requisition.STATUS_CHOICES,
        'priority_choices': Requisition.PRIORITY_CHOICES,
    }
    
    return render(request, 'requisitions/requisition_list.html', context)


@login_required
def requisition_create(request):
    """Create new requisition"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create requisition
                requisition = Requisition.objects.create(
                    title=request.POST.get('title'),
                    department_id=request.POST.get('department'),
                    budget_id=request.POST.get('budget') if request.POST.get('budget') else None,
                    requested_by=request.user,
                    justification=request.POST.get('justification'),
                    estimated_amount=Decimal(request.POST.get('estimated_amount', 0)),
                    required_date=request.POST.get('required_date'),
                    priority=request.POST.get('priority', 'MEDIUM'),
                    is_emergency=request.POST.get('is_emergency') == 'on',
                    emergency_justification=request.POST.get('emergency_justification', ''),
                    notes=request.POST.get('notes', ''),
                    status='DRAFT'
                )
                
                # Create requisition items
                items_data = json.loads(request.POST.get('items_json', '[]'))
                total_estimated = Decimal('0')
                
                for item_data in items_data:
                    item = RequisitionItem.objects.create(
                        requisition=requisition,
                        item_id=item_data.get('item_id') if item_data.get('item_id') else None,
                        item_description=item_data.get('description'),
                        specifications=item_data.get('specifications', ''),
                        quantity=Decimal(item_data.get('quantity')),
                        unit_of_measure=item_data.get('unit'),
                        estimated_unit_price=Decimal(item_data.get('unit_price')),
                        notes=item_data.get('notes', '')
                    )
                    total_estimated += item.estimated_total
                
                # Update estimated amount
                requisition.estimated_amount = total_estimated
                requisition.save()
                
                # Handle file attachments
                if request.FILES:
                    for file_key in request.FILES:
                        file = request.FILES[file_key]
                        RequisitionAttachment.objects.create(
                            requisition=requisition,
                            attachment_type=request.POST.get(f'{file_key}_type', 'OTHER'),
                            file_name=file.name,
                            file=file,
                            description=request.POST.get(f'{file_key}_description', ''),
                            uploaded_by=request.user
                        )
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    model_name='Requisition',
                    object_id=str(requisition.id),
                    object_repr=requisition.requisition_number,
                    changes={'status': 'DRAFT', 'created': True}
                )
                
                messages.success(request, f'Requisition {requisition.requisition_number} created successfully!')
                
                # Check if submit action
                if request.POST.get('action') == 'submit':
                    return redirect('requisition_submit', pk=requisition.id)
                
                return redirect('requisition_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error creating requisition: {str(e)}')
            return redirect('requisition_create')
    
    # GET request - show form
    departments = Department.objects.filter(is_active=True).order_by('name')
    budgets = Budget.objects.filter(is_active=True).select_related('category', 'department')
    items = Item.objects.filter(is_active=True).select_related('category').order_by('name')
    
    # Filter budgets by user's department if not admin
    if request.user.role not in ['ADMIN', 'PROCUREMENT', 'FINANCE']:
        if request.user.department:
            budgets = budgets.filter(department=request.user.department)
    
    context = {
        'departments': departments,
        'budgets': budgets,
        'items': items,
        'priority_choices': Requisition.PRIORITY_CHOICES,
    }
    
    return render(request, 'requisitions/requisition_create.html', context)


@login_required
def requisition_detail(request, pk):
    """View requisition details"""
    requisition = get_object_or_404(
        Requisition.objects.select_related(
            'department', 'budget', 'requested_by'
        ).prefetch_related(
            'items__item',
            'attachments',
            'approvals__approver',
            'purchase_orders'
        ),
        pk=pk
    )
    
    # Check permissions
    can_edit = False
    can_approve = False
    can_submit = False
    
    if request.user.role == 'ADMIN':
        can_edit = True
        can_approve = True
    elif request.user == requisition.requested_by and requisition.status == 'DRAFT':
        can_edit = True
        can_submit = True
    elif request.user.role == 'HOD' and request.user.department == requisition.department:
        can_approve = requisition.status == 'SUBMITTED'
    elif request.user.role == 'PROCUREMENT':
        can_approve = requisition.status in ['HOD_APPROVED', 'FACULTY_APPROVED', 'BUDGET_APPROVED']
    elif request.user.role == 'FINANCE':
        can_approve = requisition.status in ['HOD_APPROVED', 'FACULTY_APPROVED']
    
    # Get approval history
    approvals = requisition.approvals.all().order_by('sequence')
    
    # Calculate totals
    items_total = requisition.items.aggregate(Sum('estimated_total'))['estimated_total__sum'] or 0
    
    context = {
        'requisition': requisition,
        'can_edit': can_edit,
        'can_approve': can_approve,
        'can_submit': can_submit,
        'approvals': approvals,
        'items_total': items_total,
    }
    
    return render(request, 'requisitions/requisition_detail.html', context)


@login_required
def requisition_update(request, pk):
    """Update requisition"""
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Check permissions
    if requisition.status != 'DRAFT' and request.user.role != 'ADMIN':
        messages.error(request, 'You can only edit draft requisitions.')
        return redirect('requisition_detail', pk=pk)
    
    if requisition.requested_by != request.user and request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to edit this requisition.')
        return redirect('requisition_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Store old values for audit
                old_values = {
                    'title': requisition.title,
                    'estimated_amount': str(requisition.estimated_amount),
                    'status': requisition.status
                }
                
                # Update requisition
                requisition.title = request.POST.get('title')
                requisition.department_id = request.POST.get('department')
                requisition.budget_id = request.POST.get('budget') if request.POST.get('budget') else None
                requisition.justification = request.POST.get('justification')
                requisition.required_date = request.POST.get('required_date')
                requisition.priority = request.POST.get('priority', 'MEDIUM')
                requisition.is_emergency = request.POST.get('is_emergency') == 'on'
                requisition.emergency_justification = request.POST.get('emergency_justification', '')
                requisition.notes = request.POST.get('notes', '')
                
                # Delete existing items
                requisition.items.all().delete()
                
                # Create new items
                items_data = json.loads(request.POST.get('items_json', '[]'))
                total_estimated = Decimal('0')
                
                for item_data in items_data:
                    item = RequisitionItem.objects.create(
                        requisition=requisition,
                        item_id=item_data.get('item_id') if item_data.get('item_id') else None,
                        item_description=item_data.get('description'),
                        specifications=item_data.get('specifications', ''),
                        quantity=Decimal(item_data.get('quantity')),
                        unit_of_measure=item_data.get('unit'),
                        estimated_unit_price=Decimal(item_data.get('unit_price')),
                        notes=item_data.get('notes', '')
                    )
                    total_estimated += item.estimated_total
                
                requisition.estimated_amount = total_estimated
                requisition.save()
                
                # Handle new attachments
                if request.FILES:
                    for file_key in request.FILES:
                        file = request.FILES[file_key]
                        RequisitionAttachment.objects.create(
                            requisition=requisition,
                            attachment_type=request.POST.get(f'{file_key}_type', 'OTHER'),
                            file_name=file.name,
                            file=file,
                            description=request.POST.get(f'{file_key}_description', ''),
                            uploaded_by=request.user
                        )
                
                # Create audit log
                new_values = {
                    'title': requisition.title,
                    'estimated_amount': str(requisition.estimated_amount),
                    'status': requisition.status
                }
                
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Requisition',
                    object_id=str(requisition.id),
                    object_repr=requisition.requisition_number,
                    changes={'old': old_values, 'new': new_values}
                )
                
                messages.success(request, f'Requisition {requisition.requisition_number} updated successfully!')
                return redirect('requisition_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error updating requisition: {str(e)}')
    
    # GET request
    departments = Department.objects.filter(is_active=True).order_by('name')
    budgets = Budget.objects.filter(is_active=True).select_related('category', 'department')
    items = Item.objects.filter(is_active=True).select_related('category').order_by('name')
    
    context = {
        'requisition': requisition,
        'departments': departments,
        'budgets': budgets,
        'items': items,
        'priority_choices': Requisition.PRIORITY_CHOICES,
    }
    
    return render(request, 'requisitions/requisition_update.html', context)


@login_required
def requisition_delete(request, pk):
    """Delete requisition"""
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Check permissions
    if requisition.status != 'DRAFT' and request.user.role != 'ADMIN':
        messages.error(request, 'You can only delete draft requisitions.')
        return redirect('requisition_detail', pk=pk)
    
    if requisition.requested_by != request.user and request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to delete this requisition.')
        return redirect('requisition_detail', pk=pk)
    
    if request.method == 'POST':
        req_number = requisition.requisition_number
        
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Requisition',
            object_id=str(requisition.id),
            object_repr=req_number,
            changes={'deleted': True}
        )
        
        requisition.delete()
        messages.success(request, f'Requisition {req_number} deleted successfully!')
        return redirect('requisition_list')
    
    return render(request, 'requisitions/requisition_delete.html', {'requisition': requisition})


@login_required
def requisition_submit(request, pk):
    """Submit requisition for approval"""
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Check permissions
    if requisition.requested_by != request.user and request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to submit this requisition.')
        return redirect('requisition_detail', pk=pk)
    
    if requisition.status != 'DRAFT':
        messages.error(request, 'Only draft requisitions can be submitted.')
        return redirect('requisition_detail', pk=pk)
    
    if not requisition.items.exists():
        messages.error(request, 'Cannot submit requisition without items.')
        return redirect('requisition_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update status
                requisition.status = 'SUBMITTED'
                requisition.submitted_at = timezone.now()
                requisition.save()
                
                # Create approval workflow
                sequence = 1
                
                # HOD Approval
                if requisition.department.hod:
                    RequisitionApproval.objects.create(
                        requisition=requisition,
                        approval_stage='HOD',
                        approver=requisition.department.hod,
                        sequence=sequence
                    )
                    sequence += 1
                    
                    # Create notification
                    Notification.objects.create(
                        user=requisition.department.hod,
                        notification_type='APPROVAL',
                        priority='HIGH',
                        title='Requisition Pending Approval',
                        message=f'Requisition {requisition.requisition_number} requires your approval.',
                        link_url=f'/requisitions/{requisition.id}/'
                    )
                
                # Budget approval
                finance_users = User.objects.filter(role='FINANCE', is_active=True).first()
                if finance_users:
                    RequisitionApproval.objects.create(
                        requisition=requisition,
                        approval_stage='BUDGET',
                        approver=finance_users,
                        sequence=sequence
                    )
                    sequence += 1
                
                # Procurement approval
                procurement_users = User.objects.filter(role='PROCUREMENT', is_active=True).first()
                if procurement_users:
                    RequisitionApproval.objects.create(
                        requisition=requisition,
                        approval_stage='PROCUREMENT',
                        approver=procurement_users,
                        sequence=sequence
                    )
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='SUBMIT',
                    model_name='Requisition',
                    object_id=str(requisition.id),
                    object_repr=requisition.requisition_number,
                    changes={'status': 'SUBMITTED'}
                )
                
                messages.success(request, f'Requisition {requisition.requisition_number} submitted for approval!')
                return redirect('requisition_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error submitting requisition: {str(e)}')
    
    return render(request, 'requisitions/requisition_submit.html', {'requisition': requisition})


@login_required
def pending_requisitions(request):
    """View pending requisitions for approval"""
    requisitions = Requisition.objects.none()
    
    # Get requisitions based on user role
    if request.user.role == 'HOD':
        requisitions = Requisition.objects.filter(
            department=request.user.department,
            status='SUBMITTED'
        ).select_related('department', 'requested_by')
    
    elif request.user.role == 'FINANCE':
        requisitions = Requisition.objects.filter(
            status__in=['HOD_APPROVED', 'FACULTY_APPROVED']
        ).select_related('department', 'requested_by')
    
    elif request.user.role == 'PROCUREMENT':
        requisitions = Requisition.objects.filter(
            status__in=['HOD_APPROVED', 'FACULTY_APPROVED', 'BUDGET_APPROVED']
        ).select_related('department', 'requested_by')
    
    elif request.user.role == 'ADMIN':
        requisitions = Requisition.objects.filter(
            status__in=['SUBMITTED', 'HOD_APPROVED', 'FACULTY_APPROVED', 'BUDGET_APPROVED']
        ).select_related('department', 'requested_by')
    
    # Pagination
    paginator = Paginator(requisitions.order_by('-created_at'), 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    total_count = requisitions.count()
    total_amount = requisitions.aggregate(Sum('estimated_amount'))['estimated_amount__sum'] or 0
    
    context = {
        'requisitions': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'total_amount': total_amount,
    }
    
    return render(request, 'requisitions/pending_requisitions.html', context)


# API Views
@login_required
def get_budget_info(request, budget_id):
    """API: Get budget information"""
    try:
        budget = Budget.objects.select_related('category', 'department').get(id=budget_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(budget.id),
                'category': budget.category.name,
                'allocated_amount': float(budget.allocated_amount),
                'available_balance': float(budget.available_balance),
                'department': budget.department.name
            }
        })
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)


@login_required
def get_item_info(request, item_id):
    """API: Get item information"""
    try:
        item = Item.objects.select_related('category').get(id=item_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(item.id),
                'name': item.name,
                'code': item.code,
                'description': item.description,
                'unit_of_measure': item.unit_of_measure,
                'standard_price': float(item.standard_price) if item.standard_price else None,
                'specifications': item.specifications,
                'category': item.category.name
            }
        })
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)


@login_required
def delete_attachment(request, attachment_id):
    """API: Delete requisition attachment"""
    try:
        attachment = get_object_or_404(RequisitionAttachment, id=attachment_id)
        requisition = attachment.requisition
        
        # Check permissions
        if requisition.requested_by != request.user and request.user.role != 'ADMIN':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        if requisition.status != 'DRAFT':
            return JsonResponse({'success': False, 'error': 'Can only delete attachments from draft requisitions'}, status=400)
        
        attachment.delete()
        return JsonResponse({'success': True, 'message': 'Attachment deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    Tender, TenderDocument, Bid, BidItem, BidDocument, BidEvaluation,
    EvaluationCriteria, Requisition, Supplier, User, AuditLog, Notification,
    RequisitionItem
)


@login_required
def tender_list(request):
    """List all tenders with filters"""
    # Check permissions
    if request.user.role not in ['PROCUREMENT', 'ADMIN', 'HOD', 'FINANCE']:
        messages.error(request, 'You do not have permission to access tenders.')
        return redirect('dashboard')
    
    tenders = Tender.objects.select_related(
        'requisition__department', 'created_by'
    ).prefetch_related('invited_suppliers', 'bids')
    
    # Filters
    status_filter = request.GET.get('status', '')
    tender_type_filter = request.GET.get('tender_type', '')
    method_filter = request.GET.get('method', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        tenders = tenders.filter(status=status_filter)
    
    if tender_type_filter:
        tenders = tenders.filter(tender_type=tender_type_filter)
    
    if method_filter:
        tenders = tenders.filter(procurement_method=method_filter)
    
    if search_query:
        tenders = tenders.filter(
            Q(tender_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if date_from:
        tenders = tenders.filter(created_at__gte=date_from)
    
    if date_to:
        tenders = tenders.filter(created_at__lte=date_to)
    
    # Statistics
    total_count = tenders.count()
    published_count = tenders.filter(status='PUBLISHED').count()
    closed_count = tenders.filter(status='CLOSED').count()
    evaluating_count = tenders.filter(status='EVALUATING').count()
    awarded_count = tenders.filter(status='AWARDED').count()
    total_value = tenders.aggregate(Sum('estimated_budget'))['estimated_budget__sum'] or 0
    
    # Pagination
    paginator = Paginator(tenders.order_by('-created_at'), 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tenders': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'tender_type_filter': tender_type_filter,
        'method_filter': method_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': total_count,
        'published_count': published_count,
        'closed_count': closed_count,
        'evaluating_count': evaluating_count,
        'awarded_count': awarded_count,
        'total_value': total_value,
        'status_choices': Tender.STATUS_CHOICES,
        'tender_type_choices': Tender.TENDER_TYPES,
        'method_choices': Tender.METHOD_CHOICES,
    }
    
    return render(request, 'tenders/tender_list.html', context)


@login_required
def tender_create(request):
    """Create new tender"""
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to create tenders.')
        return redirect('tender_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get requisition
                requisition_id = request.POST.get('requisition')
                requisition = get_object_or_404(Requisition, id=requisition_id)
                
                # Create tender
                tender = Tender.objects.create(
                    requisition=requisition,
                    title=request.POST.get('title'),
                    tender_type=request.POST.get('tender_type'),
                    procurement_method=request.POST.get('procurement_method'),
                    description=request.POST.get('description'),
                    closing_date=request.POST.get('closing_date'),
                    bid_opening_date=request.POST.get('bid_opening_date'),
                    estimated_budget=Decimal(request.POST.get('estimated_budget')),
                    created_by=request.user,
                    status='DRAFT'
                )
                
                # Add invited suppliers if restricted tender
                if tender.procurement_method == 'RESTRICTED':
                    supplier_ids = request.POST.getlist('invited_suppliers')
                    if supplier_ids:
                        tender.invited_suppliers.set(supplier_ids)
                
                # Create evaluation criteria
                criteria_data = json.loads(request.POST.get('criteria_json', '[]'))
                for idx, criterion in enumerate(criteria_data, 1):
                    EvaluationCriteria.objects.create(
                        tender=tender,
                        criterion_name=criterion['name'],
                        criterion_type=criterion['type'],
                        description=criterion['description'],
                        weight=Decimal(criterion['weight']),
                        max_score=Decimal(criterion['max_score']),
                        is_mandatory=criterion.get('is_mandatory', False),
                        sequence=idx
                    )
                
                # Handle tender documents
                if request.FILES:
                    for file_key in request.FILES:
                        file = request.FILES[file_key]
                        TenderDocument.objects.create(
                            tender=tender,
                            document_name=file.name,
                            file=file,
                            description=request.POST.get(f'{file_key}_description', ''),
                            is_mandatory=request.POST.get(f'{file_key}_mandatory') == 'on'
                        )
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    model_name='Tender',
                    object_id=str(tender.id),
                    object_repr=tender.tender_number,
                    changes={'status': 'DRAFT', 'created': True}
                )
                
                messages.success(request, f'Tender {tender.tender_number} created successfully!')
                
                # Check if publish action
                if request.POST.get('action') == 'publish':
                    return redirect('tender_publish', pk=tender.id)
                
                return redirect('tender_detail', pk=tender.id)
                
        except Exception as e:
            messages.error(request, f'Error creating tender: {str(e)}')
            return redirect('tender_create')
    
    # GET request - show form
    # Get approved requisitions without tenders
    requisitions = Requisition.objects.filter(
        status='APPROVED',
        tenders__isnull=True
    ).select_related('department', 'requested_by')
    
    suppliers = Supplier.objects.filter(status='APPROVED').order_by('name')
    
    context = {
        'requisitions': requisitions,
        'suppliers': suppliers,
        'tender_type_choices': Tender.TENDER_TYPES,
        'method_choices': Tender.METHOD_CHOICES,
    }
    
    return render(request, 'tenders/tender_create.html', context)


@login_required
def tender_detail(request, pk):
    """View tender details"""
    tender = get_object_or_404(
        Tender.objects.select_related(
            'requisition__department', 'created_by'
        ).prefetch_related(
            'documents',
            'bids__supplier',
            'bids__evaluations',
            'evaluation_criteria',
            'invited_suppliers'
        ),
        pk=pk
    )
    
    # Check permissions
    can_edit = False
    can_publish = False
    can_evaluate = False
    can_award = False
    
    if request.user.role == 'ADMIN':
        can_edit = True
        can_publish = True
        can_evaluate = True
        can_award = True
    elif request.user.role == 'PROCUREMENT':
        can_edit = tender.status == 'DRAFT'
        can_publish = tender.status == 'DRAFT'
        can_evaluate = tender.status in ['CLOSED', 'EVALUATING']
        can_award = tender.status == 'EVALUATING'
    
    # Get bids statistics
    bids_stats = {
        'total': tender.bids.count(),
        'submitted': tender.bids.filter(status='SUBMITTED').count(),
        'qualified': tender.bids.filter(status='QUALIFIED').count(),
        'disqualified': tender.bids.filter(status='DISQUALIFIED').count(),
        'lowest_bid': tender.bids.aggregate(Min('bid_amount'))['bid_amount__min'],
        'highest_bid': tender.bids.aggregate(Max('bid_amount'))['bid_amount__max'],
        'average_bid': tender.bids.aggregate(Avg('bid_amount'))['bid_amount__avg'],
    }
    
    # Get evaluation summary
    evaluation_complete = False
    if tender.status == 'EVALUATING':
        total_bids = tender.bids.exclude(status='DISQUALIFIED').count()
        evaluated_bids = tender.bids.exclude(status='DISQUALIFIED').filter(
            evaluations__isnull=False
        ).distinct().count()
        evaluation_complete = total_bids > 0 and total_bids == evaluated_bids
    
    context = {
        'tender': tender,
        'can_edit': can_edit,
        'can_publish': can_publish,
        'can_evaluate': can_evaluate,
        'can_award': can_award,
        'bids_stats': bids_stats,
        'evaluation_complete': evaluation_complete,
    }
    
    return render(request, 'tenders/tender_detail.html', context)


@login_required
def tender_publish(request, pk):
    """Publish tender"""
    tender = get_object_or_404(Tender, pk=pk)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to publish tenders.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status != 'DRAFT':
        messages.error(request, 'Only draft tenders can be published.')
        return redirect('tender_detail', pk=pk)
    
    # Validate tender is ready
    if not tender.documents.exists():
        messages.error(request, 'Please upload tender documents before publishing.')
        return redirect('tender_detail', pk=pk)
    
    if not tender.evaluation_criteria.exists():
        messages.error(request, 'Please add evaluation criteria before publishing.')
        return redirect('tender_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tender.status = 'PUBLISHED'
                tender.publish_date = timezone.now()
                tender.save()
                
                # Create notifications for invited suppliers (if restricted)
                if tender.procurement_method == 'RESTRICTED':
                    for supplier in tender.invited_suppliers.all():
                        if supplier.user_set.exists():
                            for user in supplier.user_set.filter(role='SUPPLIER'):
                                Notification.objects.create(
                                    user=user,
                                    notification_type='TENDER',
                                    priority='HIGH',
                                    title='New Tender Invitation',
                                    message=f'You are invited to bid on tender {tender.tender_number}: {tender.title}',
                                    link_url=f'/tenders/{tender.id}/'
                                )
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Tender',
                    object_id=str(tender.id),
                    object_repr=tender.tender_number,
                    changes={'status': 'PUBLISHED', 'publish_date': str(timezone.now())}
                )
                
                messages.success(request, f'Tender {tender.tender_number} published successfully!')
                return redirect('tender_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error publishing tender: {str(e)}')
    
    return render(request, 'tenders/tender_publish.html', {'tender': tender})


@login_required
def tender_close(request, pk):
    """Close tender for bidding"""
    tender = get_object_or_404(Tender, pk=pk)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to close tenders.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status != 'PUBLISHED':
        messages.error(request, 'Only published tenders can be closed.')
        return redirect('tender_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tender.status = 'CLOSED'
                tender.save()
                
                # Update all submitted bids
                tender.bids.filter(status='SUBMITTED').update(status='OPENED')
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Tender',
                    object_id=str(tender.id),
                    object_repr=tender.tender_number,
                    changes={'status': 'CLOSED'}
                )
                
                messages.success(request, f'Tender {tender.tender_number} closed successfully! You can now proceed to evaluation.')
                return redirect('tender_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error closing tender: {str(e)}')
    
    return render(request, 'tenders/tender_close.html', {'tender': tender})


@login_required
def tender_evaluate(request, pk):
    """Start tender evaluation"""
    tender = get_object_or_404(Tender, pk=pk)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to evaluate tenders.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status not in ['CLOSED', 'EVALUATING']:
        messages.error(request, 'Only closed tenders can be evaluated.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status == 'CLOSED':
        tender.status = 'EVALUATING'
        tender.save()
    
    # Get bids for evaluation
    bids = tender.bids.exclude(status='DISQUALIFIED').select_related('supplier')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                bid_id = request.POST.get('bid_id')
                bid = get_object_or_404(Bid, id=bid_id, tender=tender)
                
                # Create evaluation
                evaluation = BidEvaluation.objects.create(
                    bid=bid,
                    evaluator=request.user,
                    technical_compliance=request.POST.get('technical_compliance') == 'on',
                    financial_compliance=request.POST.get('financial_compliance') == 'on',
                    technical_score=Decimal(request.POST.get('technical_score')),
                    financial_score=Decimal(request.POST.get('financial_score')),
                    strengths=request.POST.get('strengths', ''),
                    weaknesses=request.POST.get('weaknesses', ''),
                    recommendation=request.POST.get('recommendation')
                )
                
                # Update bid scores
                bid.technical_score = evaluation.technical_score
                bid.financial_score = evaluation.financial_score
                bid.evaluation_score = evaluation.total_score
                
                # Determine if qualified
                if evaluation.technical_compliance and evaluation.financial_compliance:
                    bid.status = 'QUALIFIED'
                else:
                    bid.status = 'DISQUALIFIED'
                    bid.disqualification_reason = request.POST.get('disqualification_reason', '')
                
                bid.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Bid',
                    object_id=str(bid.id),
                    object_repr=bid.bid_number,
                    changes={'evaluated': True, 'score': float(evaluation.total_score)}
                )
                
                messages.success(request, f'Bid {bid.bid_number} evaluated successfully!')
                return redirect('tender_evaluate', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error evaluating bid: {str(e)}')
    
    context = {
        'tender': tender,
        'bids': bids,
        'criteria': tender.evaluation_criteria.all().order_by('sequence'),
    }
    
    return render(request, 'tenders/tender_evaluate.html', context)


@login_required
def tender_award(request, pk):
    """Award tender to winning bidder"""
    tender = get_object_or_404(Tender, pk=pk)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to award tenders.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status != 'EVALUATING':
        messages.error(request, 'Only evaluated tenders can be awarded.')
        return redirect('tender_detail', pk=pk)
    
    # Get qualified bids ranked by score
    qualified_bids = tender.bids.filter(
        status='QUALIFIED'
    ).order_by('-evaluation_score', 'bid_amount')
    
    if not qualified_bids.exists():
        messages.error(request, 'No qualified bids available for award.')
        return redirect('tender_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                bid_id = request.POST.get('winning_bid')
                winning_bid = get_object_or_404(Bid, id=bid_id, tender=tender)
                
                # Update tender status
                tender.status = 'AWARDED'
                tender.save()
                
                # Update winning bid
                winning_bid.status = 'AWARDED'
                winning_bid.save()
                
                # Rank all qualified bids
                for idx, bid in enumerate(qualified_bids, 1):
                    bid.rank = idx
                    if bid.id != winning_bid.id:
                        bid.status = 'REJECTED'
                    bid.save()
                
                # Create notification for winning supplier
                if winning_bid.supplier.user_set.exists():
                    for user in winning_bid.supplier.user_set.filter(role='SUPPLIER'):
                        Notification.objects.create(
                            user=user,
                            notification_type='TENDER',
                            priority='URGENT',
                            title='Tender Award',
                            message=f'Congratulations! Your bid {winning_bid.bid_number} has been awarded for tender {tender.tender_number}',
                            link_url=f'/bids/{winning_bid.id}/'
                        )
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Tender',
                    object_id=str(tender.id),
                    object_repr=tender.tender_number,
                    changes={'status': 'AWARDED', 'winning_bid': winning_bid.bid_number}
                )
                
                messages.success(request, f'Tender {tender.tender_number} awarded to {winning_bid.supplier.name}!')
                return redirect('tender_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error awarding tender: {str(e)}')
    
    context = {
        'tender': tender,
        'qualified_bids': qualified_bids,
    }
    
    return render(request, 'tenders/tender_award.html', context)


@login_required
def tender_cancel(request, pk):
    """Cancel tender"""
    tender = get_object_or_404(Tender, pk=pk)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to cancel tenders.')
        return redirect('tender_detail', pk=pk)
    
    if tender.status == 'AWARDED':
        messages.error(request, 'Cannot cancel awarded tenders.')
        return redirect('tender_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                cancellation_reason = request.POST.get('cancellation_reason')
                
                # Update tender status
                old_status = tender.status
                tender.status = 'CANCELLED'
                tender.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Tender',
                    object_id=str(tender.id),
                    object_repr=tender.tender_number,
                    changes={
                        'status': 'CANCELLED',
                        'old_status': old_status,
                        'reason': cancellation_reason
                    }
                )
                
                messages.success(request, f'Tender {tender.tender_number} cancelled successfully!')
                return redirect('tender_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error cancelling tender: {str(e)}')
    
    return render(request, 'tenders/tender_cancel.html', {'tender': tender})


# BID MANAGEMENT VIEWS

@login_required
def bid_list(request, tender_id):
    """List all bids for a tender"""
    tender = get_object_or_404(Tender, pk=tender_id)
    
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to view bids.')
        return redirect('tender_detail', pk=tender_id)
    
    bids = tender.bids.select_related('supplier').prefetch_related(
        'items', 'documents', 'evaluations'
    ).order_by('-submitted_at')
    
    # Filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        bids = bids.filter(status=status_filter)
    
    # Statistics
    stats = {
        'total': bids.count(),
        'submitted': bids.filter(status='SUBMITTED').count(),
        'qualified': bids.filter(status='QUALIFIED').count(),
        'disqualified': bids.filter(status='DISQUALIFIED').count(),
        'average_amount': bids.aggregate(Avg('bid_amount'))['bid_amount__avg'],
    }
    
    context = {
        'tender': tender,
        'bids': bids,
        'status_filter': status_filter,
        'stats': stats,
    }
    
    return render(request, 'tenders/bid_list.html', context)


@login_required
def bid_detail(request, pk):
    """View bid details"""
    bid = get_object_or_404(
        Bid.objects.select_related(
            'tender', 'supplier'
        ).prefetch_related(
            'items__requisition_item',
            'documents',
            'evaluations__evaluator'
        ),
        pk=pk
    )
    
    # Check permissions
    if request.user.role not in ['PROCUREMENT', 'ADMIN']:
        # Suppliers can only view their own bids
        if request.user.role == 'SUPPLIER':
            if not bid.supplier.user_set.filter(id=request.user.id).exists():
                messages.error(request, 'You do not have permission to view this bid.')
                return redirect('dashboard')
        else:
            messages.error(request, 'You do not have permission to view bids.')
            return redirect('dashboard')
    
    # Calculate totals
    items_total = bid.items.aggregate(Sum('quoted_total'))['quoted_total__sum'] or 0
    
    context = {
        'bid': bid,
        'items_total': items_total,
    }
    
    return render(request, 'tenders/bid_detail.html', context)


# API ENDPOINTS

@login_required
def get_requisition_items(request, requisition_id):
    """API: Get requisition items for tender creation"""
    try:
        requisition = Requisition.objects.get(id=requisition_id)
        items = requisition.items.all().select_related('item')
        
        items_data = [{
            'id': str(item.id),
            'description': item.item_description,
            'specifications': item.specifications,
            'quantity': float(item.quantity),
            'unit': item.unit_of_measure,
            'estimated_price': float(item.estimated_unit_price),
        } for item in items]
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'total': float(requisition.estimated_amount)
        })
    except Requisition.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Requisition not found'}, status=404)


@login_required
def get_tender_statistics(request):
    """API: Get tender statistics for dashboard"""
    try:
        stats = {
            'total_tenders': Tender.objects.count(),
            'active_tenders': Tender.objects.filter(status='PUBLISHED').count(),
            'closed_tenders': Tender.objects.filter(status='CLOSED').count(),
            'awarded_tenders': Tender.objects.filter(status='AWARDED').count(),
            'total_value': float(Tender.objects.aggregate(Sum('estimated_budget'))['estimated_budget__sum'] or 0),
            'average_bids': float(Tender.objects.annotate(
                bid_count=Count('bids')
            ).aggregate(Avg('bid_count'))['bid_count__avg'] or 0),
        }
        
        return JsonResponse({'success': True, 'data': stats})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, F
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import json

from .models import (
    PurchaseOrder, PurchaseOrderItem, Requisition, Supplier, 
    Bid, POAmendment, User, Department, Budget, GoodsReceivedNote,
    Invoice, StockMovement
)


@login_required
def po_dashboard(request):
    """Purchase Order Dashboard with statistics and charts"""
    
    # Date filters
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    current_year = today.year
    
    # Basic statistics
    total_pos = PurchaseOrder.objects.count()
    pending_pos = PurchaseOrder.objects.filter(
        status__in=['DRAFT', 'PENDING_APPROVAL']
    ).count()
    active_pos = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIAL_DELIVERY']
    ).count()
    
    # Financial statistics
    total_po_value = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIAL_DELIVERY', 'DELIVERED', 'CLOSED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_value = PurchaseOrder.objects.filter(
        po_date__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Status distribution
    status_data = PurchaseOrder.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_chart = {
        'labels': [dict(PurchaseOrder.STATUS_CHOICES).get(item['status'], item['status']) 
                   for item in status_data],
        'values': [item['count'] for item in status_data]
    }
    
    # Monthly PO trend (last 6 months)
    months = []
    po_counts = []
    po_values = []
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i > 0:
            next_month = month_date.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        else:
            month_end = today
            
        month_pos = PurchaseOrder.objects.filter(
            po_date__gte=month_start,
            po_date__lte=month_end
        )
        
        months.append(month_start.strftime('%b %Y'))
        po_counts.append(month_pos.count())
        po_values.append(float(month_pos.aggregate(
            total=Sum('total_amount'))['total'] or 0))
    
    po_trend_chart = {
        'labels': months,
        'counts': po_counts,
        'values': po_values
    }
    
    # Top suppliers by PO value
    top_suppliers = PurchaseOrder.objects.values(
        'supplier__name'
    ).annotate(
        total_value=Sum('total_amount'),
        po_count=Count('id')
    ).order_by('-total_value')[:5]
    
    supplier_chart = {
        'labels': [item['supplier__name'] for item in top_suppliers],
        'values': [float(item['total_value']) for item in top_suppliers],
        'counts': [item['po_count'] for item in top_suppliers]
    }
    
    # Department spend
    dept_spend = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED', 'CLOSED']
    ).values(
        'requisition__department__name'
    ).annotate(
        total_spend=Sum('total_amount')
    ).order_by('-total_spend')[:8]
    
    dept_chart = {
        'labels': [item['requisition__department__name'] or 'N/A' 
                   for item in dept_spend],
        'values': [float(item['total_spend']) for item in dept_spend]
    }
    
    # Recent POs
    recent_pos = PurchaseOrder.objects.select_related(
        'supplier', 'requisition', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Pending approvals
    pending_approvals = PurchaseOrder.objects.filter(
        status='PENDING_APPROVAL'
    ).select_related('supplier', 'requisition').order_by('-created_at')[:5]
    
    # Delivery tracking
    pending_delivery = PurchaseOrder.objects.filter(
        status__in=['SENT', 'ACKNOWLEDGED', 'PARTIAL_DELIVERY'],
        delivery_date__lte=today + timedelta(days=7)
    ).select_related('supplier').order_by('delivery_date')[:10]
    
    # Performance metrics
    avg_po_value = PurchaseOrder.objects.filter(
        status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED', 'CLOSED']
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Delivery performance
    delivered_pos = PurchaseOrder.objects.filter(status='DELIVERED')
    on_time_delivery = delivered_pos.filter(
        delivery_date__gte=F('po_date')
    ).count()
    total_delivered = delivered_pos.count()
    delivery_rate = (on_time_delivery / total_delivered * 100) if total_delivered > 0 else 0
    
    context = {
        'total_pos': total_pos,
        'pending_pos': pending_pos,
        'active_pos': active_pos,
        'total_po_value': total_po_value,
        'monthly_value': monthly_value,
        'avg_po_value': avg_po_value,
        'delivery_rate': round(delivery_rate, 1),
        'status_chart': status_chart,
        'po_trend_chart': po_trend_chart,
        'supplier_chart': supplier_chart,
        'dept_chart': dept_chart,
        'recent_pos': recent_pos,
        'pending_approvals': pending_approvals,
        'pending_delivery': pending_delivery,
    }
    
    return render(request, 'procurement/po_dashboard.html', context)


@login_required
def po_list(request):
    """List all purchase orders with filtering and search"""
    
    pos = PurchaseOrder.objects.select_related(
        'supplier', 'requisition', 'created_by', 'approved_by'
    ).all()
    
    # Filters
    status_filter = request.GET.get('status')
    supplier_filter = request.GET.get('supplier')
    department_filter = request.GET.get('department')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status_filter:
        pos = pos.filter(status=status_filter)
    
    if supplier_filter:
        pos = pos.filter(supplier_id=supplier_filter)
    
    if department_filter:
        pos = pos.filter(requisition__department_id=department_filter)
    
    if date_from:
        pos = pos.filter(po_date__gte=date_from)
    
    if date_to:
        pos = pos.filter(po_date__lte=date_to)
    
    if search:
        pos = pos.filter(
            Q(po_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(requisition__requisition_number__icontains=search)
        )
    
    pos = pos.order_by('-created_at')
    
    # Get filter options
    suppliers = Supplier.objects.filter(status='APPROVED').order_by('name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # Statistics for current filter
    total_value = pos.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'pos': pos,
        'suppliers': suppliers,
        'departments': departments,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'total_value': total_value,
        'filters': {
            'status': status_filter,
            'supplier': supplier_filter,
            'department': department_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'procurement/po_list.html', context)


@login_required
def po_detail(request, po_id):
    """Purchase Order detail view"""
    
    po = get_object_or_404(
        PurchaseOrder.objects.select_related(
            'supplier', 'requisition', 'bid', 'created_by', 'approved_by'
        ),
        id=po_id
    )
    
    # Get PO items
    po_items = po.items.select_related('requisition_item').all()
    
    # Get amendments
    amendments = po.amendments.select_related(
        'requested_by', 'approved_by'
    ).order_by('-created_at')
    
    # Get GRNs
    grns = po.grns.select_related('store', 'received_by').order_by('-created_at')
    
    # Get invoices
    invoices = po.invoices.select_related('supplier').order_by('-created_at')
    
    # Calculate delivery progress
    total_items = po_items.count()
    items_delivered = po_items.filter(
        quantity_delivered__gte=F('quantity')
    ).count()
    delivery_progress = (items_delivered / total_items * 100) if total_items > 0 else 0
    
    # Calculate invoice status
    total_invoiced = invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    invoice_progress = (total_invoiced / po.total_amount * 100) if po.total_amount > 0 else 0
    
    context = {
        'po': po,
        'po_items': po_items,
        'amendments': amendments,
        'grns': grns,
        'invoices': invoices,
        'delivery_progress': round(delivery_progress, 1),
        'invoice_progress': round(invoice_progress, 1),
    }
    
    return render(request, 'procurement/po_detail.html', context)


@login_required
def po_create(request):
    """Create new purchase order from approved requisition"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                requisition_id = request.POST.get('requisition')
                supplier_id = request.POST.get('supplier')
                bid_id = request.POST.get('bid')
                delivery_date = request.POST.get('delivery_date')
                delivery_address = request.POST.get('delivery_address')
                payment_terms = request.POST.get('payment_terms')
                warranty_terms = request.POST.get('warranty_terms', '')
                special_instructions = request.POST.get('special_instructions', '')
                
                # Validate
                requisition = get_object_or_404(Requisition, id=requisition_id)
                supplier = get_object_or_404(Supplier, id=supplier_id)
                
                # Check if requisition is approved
                if requisition.status != 'APPROVED':
                    messages.error(request, 'Requisition must be fully approved')
                    return redirect('po_create')
                
                # Check if PO already exists for this requisition
                if PurchaseOrder.objects.filter(requisition=requisition).exists():
                    messages.warning(request, 'Purchase order already exists for this requisition')
                    return redirect('po_list')
                
                # Get bid if provided
                bid = None
                if bid_id:
                    bid = get_object_or_404(Bid, id=bid_id)
                
                # Create PO
                po = PurchaseOrder.objects.create(
                    requisition=requisition,
                    supplier=supplier,
                    bid=bid,
                    delivery_date=delivery_date,
                    delivery_address=delivery_address,
                    payment_terms=payment_terms,
                    warranty_terms=warranty_terms,
                    special_instructions=special_instructions,
                    subtotal=0,
                    tax_amount=0,
                    total_amount=0,
                    status='DRAFT',
                    created_by=request.user
                )
                
                # Create PO items from requisition items
                req_items = requisition.items.all()
                subtotal = Decimal('0.00')
                
                for req_item in req_items:
                    # Get price from bid if available
                    unit_price = req_item.estimated_unit_price
                    
                    if bid:
                        bid_item = bid.items.filter(
                            requisition_item=req_item
                        ).first()
                        if bid_item:
                            unit_price = bid_item.quoted_unit_price
                    
                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        requisition_item=req_item,
                        item_description=req_item.item_description,
                        specifications=req_item.specifications,
                        quantity=req_item.quantity,
                        unit_of_measure=req_item.unit_of_measure,
                        unit_price=unit_price,
                        total_price=req_item.quantity * unit_price
                    )
                    
                    subtotal += req_item.quantity * unit_price
                
                # Calculate tax (assuming 16% VAT)
                tax_rate = Decimal('0.16')
                tax_amount = subtotal * tax_rate
                total_amount = subtotal + tax_amount
                
                # Update PO totals
                po.subtotal = subtotal
                po.tax_amount = tax_amount
                po.total_amount = total_amount
                po.save()
                
                # Update budget commitment
                if requisition.budget:
                    budget = requisition.budget
                    budget.committed_amount += total_amount
                    budget.save()
                
                messages.success(request, f'Purchase Order {po.po_number} created successfully')
                return redirect('po_detail', po_id=po.id)
                
        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')
            return redirect('po_create')
    
    # GET request
    # Get approved requisitions without PO
    approved_requisitions = Requisition.objects.filter(
        status='APPROVED'
    ).exclude(
        id__in=PurchaseOrder.objects.values_list('requisition_id', flat=True)
    ).select_related('department', 'requested_by')
    
    suppliers = Supplier.objects.filter(status='APPROVED').order_by('name')
    
    context = {
        'approved_requisitions': approved_requisitions,
        'suppliers': suppliers,
    }
    
    return render(request, 'procurement/po_create.html', context)


@login_required
def po_update(request, po_id):
    """Update purchase order (only in DRAFT status)"""
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Check if PO can be edited
    if po.status not in ['DRAFT', 'PENDING_APPROVAL']:
        messages.error(request, 'This purchase order cannot be edited')
        return redirect('po_detail', po_id=po.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update PO fields
                po.delivery_date = request.POST.get('delivery_date')
                po.delivery_address = request.POST.get('delivery_address')
                po.payment_terms = request.POST.get('payment_terms')
                po.warranty_terms = request.POST.get('warranty_terms', '')
                po.special_instructions = request.POST.get('special_instructions', '')
                po.save()
                
                messages.success(request, 'Purchase order updated successfully')
                return redirect('po_detail', po_id=po.id)
                
        except Exception as e:
            messages.error(request, f'Error updating purchase order: {str(e)}')
    
    context = {
        'po': po,
        'po_items': po.items.all()
    }
    
    return render(request, 'procurement/po_update.html', context)


@login_required
def po_approve(request, po_id):
    """Approve purchase order"""
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Check permission (should be procurement/finance officer)
    if request.user.role not in ['PROCUREMENT', 'FINANCE', 'ADMIN']:
        messages.error(request, 'You do not have permission to approve purchase orders')
        return redirect('po_detail', po_id=po.id)
    
    if po.status != 'PENDING_APPROVAL':
        messages.error(request, 'This purchase order is not pending approval')
        return redirect('po_detail', po_id=po.id)
    
    if request.method == 'POST':
        po.status = 'APPROVED'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()
        
        messages.success(request, f'Purchase Order {po.po_number} approved successfully')
        return redirect('po_detail', po_id=po.id)
    
    return render(request, 'procurement/po_approve.html', {'po': po})


@login_required
def po_send(request, po_id):
    """Send PO to supplier"""
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if po.status != 'APPROVED':
        messages.error(request, 'Only approved POs can be sent to suppliers')
        return redirect('po_detail', po_id=po.id)
    
    if request.method == 'POST':
        po.status = 'SENT'
        po.sent_at = timezone.now()
        po.save()
        
        # TODO: Send email to supplier
        
        messages.success(request, f'Purchase Order {po.po_number} sent to supplier')
        return redirect('po_detail', po_id=po.id)
    
    return render(request, 'procurement/po_send.html', {'po': po})


@login_required
def po_cancel(request, po_id):
    """Cancel purchase order"""
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Check if PO can be cancelled
    if po.status in ['DELIVERED', 'CLOSED']:
        messages.error(request, 'This purchase order cannot be cancelled')
        return redirect('po_detail', po_id=po.id)
    
    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason')
        
        with transaction.atomic():
            po.status = 'CANCELLED'
            po.save()
            
            # Release budget commitment
            if po.requisition.budget:
                budget = po.requisition.budget
                budget.committed_amount -= po.total_amount
                budget.save()
            
            messages.success(request, f'Purchase Order {po.po_number} cancelled')
            return redirect('po_detail', po_id=po.id)
    
    context = {'po': po}
    return render(request, 'procurement/po_cancel.html', context)


@login_required
def po_amendment_create(request, po_id):
    """Create PO amendment"""
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                amendment_type = request.POST.get('amendment_type')
                description = request.POST.get('description')
                justification = request.POST.get('justification')
                old_value = request.POST.get('old_value')
                new_value = request.POST.get('new_value')
                amount_change = Decimal(request.POST.get('amount_change', '0'))
                
                # Generate amendment number
                last_amendment = po.amendments.order_by('-created_at').first()
                if last_amendment:
                    last_num = int(last_amendment.amendment_number.split('-')[-1])
                    amendment_number = f"{po.po_number}-AMD-{last_num + 1:03d}"
                else:
                    amendment_number = f"{po.po_number}-AMD-001"
                
                POAmendment.objects.create(
                    purchase_order=po,
                    amendment_number=amendment_number,
                    amendment_type=amendment_type,
                    description=description,
                    justification=justification,
                    old_value=old_value,
                    new_value=new_value,
                    amount_change=amount_change,
                    requested_by=request.user
                )
                
                messages.success(request, 'Amendment request created successfully')
                return redirect('po_detail', po_id=po.id)
                
        except Exception as e:
            messages.error(request, f'Error creating amendment: {str(e)}')
    
    context = {
        'po': po,
        'amendment_types': POAmendment.AMENDMENT_TYPES
    }
    
    return render(request, 'procurement/po_amendment_create.html', context)


# AJAX endpoints

@login_required
def get_requisition_details(request, req_id):
    """Get requisition details for PO creation"""
    
    requisition = get_object_or_404(Requisition, id=req_id)
    
    items = []
    for item in requisition.items.all():
        items.append({
            'id': str(item.id),
            'description': item.item_description,
            'quantity': float(item.quantity),
            'unit': item.unit_of_measure,
            'price': float(item.estimated_unit_price),
            'total': float(item.estimated_total)
        })
    
    data = {
        'number': requisition.requisition_number,
        'department': requisition.department.name,
        'estimated_amount': float(requisition.estimated_amount),
        'items': items
    }
    
    return JsonResponse(data)


@login_required
def get_supplier_bids(request, req_id, supplier_id):
    """Get supplier bids for a requisition"""
    
    bids = Bid.objects.filter(
        tender__requisition_id=req_id,
        supplier_id=supplier_id,
        status='AWARDED'
    ).select_related('tender')
    
    bid_list = []
    for bid in bids:
        bid_list.append({
            'id': str(bid.id),
            'bid_number': bid.bid_number,
            'amount': float(bid.bid_amount),
            'tender': bid.tender.tender_number
        })
    
    return JsonResponse({'bids': bid_list})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import json

from .models import (
    Budget, BudgetYear, BudgetCategory, BudgetReallocation,
    Invoice, InvoiceItem, Payment, PurchaseOrder, Requisition,
    Department, Supplier, User, GoodsReceivedNote
)


# ============================================================================
# FINANCE DASHBOARD
# ============================================================================

@login_required
def finance_dashboard(request):
    """Main finance dashboard with key metrics and charts"""
    
    today = timezone.now().date()
    current_year = BudgetYear.objects.filter(is_active=True).first()
    
    # Budget Overview
    total_allocated = Budget.objects.filter(
        budget_year=current_year,
        is_active=True
    ).aggregate(total=Sum('allocated_amount'))['total'] or 0
    
    total_committed = Budget.objects.filter(
        budget_year=current_year,
        is_active=True
    ).aggregate(total=Sum('committed_amount'))['total'] or 0
    
    total_spent = Budget.objects.filter(
        budget_year=current_year,
        is_active=True
    ).aggregate(total=Sum('actual_spent'))['total'] or 0
    
    available_budget = total_allocated - total_committed - total_spent
    utilization_rate = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
    
    # Invoice Statistics
    pending_invoices = Invoice.objects.filter(
        status__in=['SUBMITTED', 'VERIFYING']
    ).count()
    
    approved_invoices_value = Invoice.objects.filter(
        status='APPROVED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Payment Statistics
    pending_payments = Payment.objects.filter(
        status='PENDING'
    ).count()
    
    payments_this_month = Payment.objects.filter(
        payment_date__month=today.month,
        payment_date__year=today.year,
        status='COMPLETED'
    ).aggregate(total=Sum('payment_amount'))['total'] or 0
    
    # Budget Utilization by Department (Top 10)
    dept_utilization = Budget.objects.filter(
        budget_year=current_year
    ).values(
        'department__name'
    ).annotate(
        allocated=Sum('allocated_amount'),
        spent=Sum('actual_spent'),
        utilization=Sum('actual_spent') / Sum('allocated_amount') * 100
    ).order_by('-spent')[:10]
    
    dept_chart = {
        'labels': [item['department__name'] for item in dept_utilization],
        'allocated': [float(item['allocated']) for item in dept_utilization],
        'spent': [float(item['spent']) for item in dept_utilization]
    }
    
    # Budget by Category
    category_budget = Budget.objects.filter(
        budget_year=current_year
    ).values(
        'category__name'
    ).annotate(
        total=Sum('allocated_amount')
    ).order_by('-total')[:8]
    
    category_chart = {
        'labels': [item['category__name'] for item in category_budget],
        'values': [float(item['total']) for item in category_budget]
    }
    
    # Monthly Expenditure Trend (Last 6 months)
    months = []
    expenditure = []
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i > 0:
            next_month = month_date.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        else:
            month_end = today
            
        month_spend = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end,
            status='COMPLETED'
        ).aggregate(total=Sum('payment_amount'))['total'] or 0
        
        months.append(month_start.strftime('%b %Y'))
        expenditure.append(float(month_spend))
    
    expenditure_chart = {
        'labels': months,
        'values': expenditure
    }
    
    # Invoice Status Distribution
    invoice_status = Invoice.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    invoice_chart = {
        'labels': [dict(Invoice.STATUS_CHOICES).get(item['status'], item['status']) 
                   for item in invoice_status],
        'values': [item['count'] for item in invoice_status]
    }
    
    # Recent Activities
    recent_invoices = Invoice.objects.select_related(
        'supplier', 'purchase_order'
    ).order_by('-created_at')[:5]
    
    recent_payments = Payment.objects.select_related(
        'invoice__supplier'
    ).order_by('-created_at')[:5]
    
    # Pending Approvals
    pending_invoice_approvals = Invoice.objects.filter(
        status='VERIFYING'
    ).select_related('supplier')[:5]
    
    context = {
        'current_year': current_year,
        'total_allocated': total_allocated,
        'total_committed': total_committed,
        'total_spent': total_spent,
        'available_budget': available_budget,
        'utilization_rate': round(utilization_rate, 1),
        'pending_invoices': pending_invoices,
        'approved_invoices_value': approved_invoices_value,
        'pending_payments': pending_payments,
        'payments_this_month': payments_this_month,
        'dept_chart': dept_chart,
        'category_chart': category_chart,
        'expenditure_chart': expenditure_chart,
        'invoice_chart': invoice_chart,
        'recent_invoices': recent_invoices,
        'recent_payments': recent_payments,
        'pending_invoice_approvals': pending_invoice_approvals,
    }
    
    return render(request, 'finance/dashboard.html', context)


# ============================================================================
# BUDGET MANAGEMENT
# ============================================================================

@login_required
def budget_list(request):
    """List all budgets with filtering"""
    
    budgets = Budget.objects.select_related(
        'budget_year', 'department', 'category', 'created_by'
    ).all()
    
    # Filters
    year_filter = request.GET.get('year')
    department_filter = request.GET.get('department')
    category_filter = request.GET.get('category')
    budget_type_filter = request.GET.get('budget_type')
    search = request.GET.get('search')
    
    if year_filter:
        budgets = budgets.filter(budget_year_id=year_filter)
    
    if department_filter:
        budgets = budgets.filter(department_id=department_filter)
    
    if category_filter:
        budgets = budgets.filter(category_id=category_filter)
    
    if budget_type_filter:
        budgets = budgets.filter(budget_type=budget_type_filter)
    
    if search:
        budgets = budgets.filter(
            Q(department__name__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    budgets = budgets.order_by('-created_at')
    
    # Calculate totals
    total_allocated = budgets.aggregate(total=Sum('allocated_amount'))['total'] or 0
    total_spent = budgets.aggregate(total=Sum('actual_spent'))['total'] or 0
    total_available = sum(b.available_balance for b in budgets)
    
    # Get filter options
    budget_years = BudgetYear.objects.all().order_by('-start_date')
    departments = Department.objects.filter(is_active=True).order_by('name')
    categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'budgets': budgets,
        'budget_years': budget_years,
        'departments': departments,
        'categories': categories,
        'budget_types': Budget.BUDGET_TYPE,
        'total_allocated': total_allocated,
        'total_spent': total_spent,
        'total_available': total_available,
        'filters': {
            'year': year_filter,
            'department': department_filter,
            'category': category_filter,
            'budget_type': budget_type_filter,
            'search': search,
        }
    }
    
    return render(request, 'finance/budget_list.html', context)


@login_required
def budget_detail(request, budget_id):
    """Budget detail view with utilization tracking"""
    
    budget = get_object_or_404(
        Budget.objects.select_related(
            'budget_year', 'department', 'category', 'created_by'
        ),
        id=budget_id
    )
    
    # Get requisitions using this budget
    requisitions = budget.requisitions.select_related(
        'requested_by', 'department'
    ).order_by('-created_at')
    
    # Get reallocations
    reallocations_from = budget.reallocations_from.select_related(
        'to_budget__department', 'requested_by', 'approved_by'
    ).order_by('-created_at')
    
    reallocations_to = budget.reallocations_to.select_related(
        'from_budget__department', 'requested_by', 'approved_by'
    ).order_by('-created_at')
    
    # Calculate utilization percentage
    utilization = (budget.actual_spent / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
    commitment = (budget.committed_amount / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
    
    context = {
        'budget': budget,
        'requisitions': requisitions,
        'reallocations_from': reallocations_from,
        'reallocations_to': reallocations_to,
        'utilization': round(utilization, 1),
        'commitment': round(commitment, 1),
    }
    
    return render(request, 'finance/budget_detail.html', context)


@login_required
def budget_create(request):
    """Create new budget allocation"""
    
    if request.user.role not in ['FINANCE', 'ADMIN']:
        messages.error(request, 'You do not have permission to create budgets')
        return redirect('budget_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                budget_year_id = request.POST.get('budget_year')
                department_id = request.POST.get('department')
                category_id = request.POST.get('category')
                budget_type = request.POST.get('budget_type')
                allocated_amount = Decimal(request.POST.get('allocated_amount'))
                reference_number = request.POST.get('reference_number', '')
                description = request.POST.get('description', '')
                
                # Check for duplicate
                if Budget.objects.filter(
                    budget_year_id=budget_year_id,
                    department_id=department_id,
                    category_id=category_id,
                    reference_number=reference_number
                ).exists():
                    messages.error(request, 'Budget already exists for this combination')
                    return redirect('budget_create')
                
                Budget.objects.create(
                    budget_year_id=budget_year_id,
                    department_id=department_id,
                    category_id=category_id,
                    budget_type=budget_type,
                    allocated_amount=allocated_amount,
                    reference_number=reference_number,
                    description=description,
                    created_by=request.user
                )
                
                messages.success(request, 'Budget created successfully')
                return redirect('budget_list')
                
        except Exception as e:
            messages.error(request, f'Error creating budget: {str(e)}')
    
    # GET request
    budget_years = BudgetYear.objects.all().order_by('-start_date')
    departments = Department.objects.filter(is_active=True).order_by('name')
    categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'budget_years': budget_years,
        'departments': departments,
        'categories': categories,
        'budget_types': Budget.BUDGET_TYPE,
    }
    
    return render(request, 'finance/budget_create.html', context)


@login_required
def budget_reallocation_create(request, budget_id):
    """Create budget reallocation request"""
    
    from_budget = get_object_or_404(Budget, id=budget_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                to_budget_id = request.POST.get('to_budget')
                amount = Decimal(request.POST.get('amount'))
                justification = request.POST.get('justification')
                
                to_budget = get_object_or_404(Budget, id=to_budget_id)
                
                # Validate amount
                if amount > from_budget.available_balance:
                    messages.error(request, 'Insufficient available budget')
                    return redirect('budget_reallocation_create', budget_id=budget_id)
                
                BudgetReallocation.objects.create(
                    from_budget=from_budget,
                    to_budget=to_budget,
                    amount=amount,
                    justification=justification,
                    requested_by=request.user
                )
                
                messages.success(request, 'Reallocation request submitted successfully')
                return redirect('budget_detail', budget_id=budget_id)
                
        except Exception as e:
            messages.error(request, f'Error creating reallocation: {str(e)}')
    
    # GET request - get available budgets in same year
    available_budgets = Budget.objects.filter(
        budget_year=from_budget.budget_year,
        is_active=True
    ).exclude(id=budget_id).select_related('department', 'category')
    
    context = {
        'from_budget': from_budget,
        'available_budgets': available_budgets,
    }
    
    return render(request, 'finance/budget_reallocation_create.html', context)


# ============================================================================
# INVOICE MANAGEMENT
# ============================================================================

@login_required
def invoice_list(request):
    """List all invoices with filtering"""
    
    invoices = Invoice.objects.select_related(
        'supplier', 'purchase_order', 'verified_by', 'approved_by'
    ).all()
    
    # Filters
    status_filter = request.GET.get('status')
    supplier_filter = request.GET.get('supplier')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    if supplier_filter:
        invoices = invoices.filter(supplier_id=supplier_filter)
    
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)
    
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(supplier_invoice_number__icontains=search) |
            Q(supplier__name__icontains=search)
        )
    
    invoices = invoices.order_by('-created_at')
    
    # Statistics
    total_value = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
    pending_value = invoices.filter(
        status__in=['SUBMITTED', 'VERIFYING']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get filter options
    suppliers = Supplier.objects.filter(status='APPROVED').order_by('name')
    
    context = {
        'invoices': invoices,
        'suppliers': suppliers,
        'status_choices': Invoice.STATUS_CHOICES,
        'total_value': total_value,
        'pending_value': pending_value,
        'filters': {
            'status': status_filter,
            'supplier': supplier_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'finance/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """Invoice detail view with 3-way matching"""
    
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'supplier', 'purchase_order', 'grn',
            'verified_by', 'approved_by', 'submitted_by'
        ),
        id=invoice_id
    )
    
    # Get invoice items
    invoice_items = invoice.items.select_related('po_item').all()
    
    # Get payments
    payments = invoice.payments.select_related(
        'processed_by', 'approved_by'
    ).order_by('-created_at')
    
    # Calculate matching status
    if invoice.purchase_order and invoice.grn:
        po_match = abs(invoice.total_amount - invoice.purchase_order.total_amount) < Decimal('0.01')
        grn_match = invoice.grn.status == 'ACCEPTED'
        three_way_match = po_match and grn_match
    else:
        po_match = False
        grn_match = False
        three_way_match = False
    
    # Payment status
    total_paid = payments.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('payment_amount'))['total'] or 0
    
    payment_progress = (total_paid / invoice.total_amount * 100) if invoice.total_amount > 0 else 0
    
    context = {
        'invoice': invoice,
        'invoice_items': invoice_items,
        'payments': payments,
        'po_match': po_match,
        'grn_match': grn_match,
        'three_way_match': three_way_match,
        'total_paid': total_paid,
        'payment_progress': round(payment_progress, 1),
    }
    
    return render(request, 'finance/invoice_detail.html', context)


@login_required
def invoice_verify(request, invoice_id):
    """Verify invoice details"""
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.user.role not in ['FINANCE', 'PROCUREMENT', 'ADMIN']:
        messages.error(request, 'You do not have permission to verify invoices')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if invoice.status != 'SUBMITTED':
        messages.error(request, 'This invoice cannot be verified')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            invoice.status = 'MATCHED'
            invoice.verified_by = request.user
            invoice.verified_at = timezone.now()
            invoice.matching_notes = notes
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} verified successfully')
        elif action == 'dispute':
            invoice.status = 'DISPUTED'
            invoice.dispute_reason = notes
            invoice.save()
            
            messages.warning(request, f'Invoice {invoice.invoice_number} marked as disputed')
        
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    context = {'invoice': invoice}
    return render(request, 'finance/invoice_verify.html', context)


@login_required
def invoice_approve(request, invoice_id):
    """Approve invoice for payment"""
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.user.role not in ['FINANCE', 'ADMIN']:
        messages.error(request, 'You do not have permission to approve invoices')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if invoice.status != 'MATCHED':
        messages.error(request, 'Invoice must be verified and matched before approval')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if request.method == 'POST':
        invoice.status = 'APPROVED'
        invoice.approved_by = request.user
        invoice.approved_at = timezone.now()
        invoice.save()
        
        messages.success(request, f'Invoice {invoice.invoice_number} approved for payment')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    context = {'invoice': invoice}
    return render(request, 'finance/invoice_approve.html', context)


# ============================================================================
# PAYMENT MANAGEMENT
# ============================================================================

@login_required
def payment_list(request):
    """List all payments with filtering"""
    
    payments = Payment.objects.select_related(
        'invoice__supplier', 'processed_by', 'approved_by'
    ).all()
    
    # Filters
    status_filter = request.GET.get('status')
    method_filter = request.GET.get('method')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if method_filter:
        payments = payments.filter(payment_method=method_filter)
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(payment_reference__icontains=search) |
            Q(invoice__supplier__name__icontains=search)
        )
    
    payments = payments.order_by('-created_at')
    
    # Statistics
    total_paid = payments.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('payment_amount'))['total'] or 0
    
    pending_amount = payments.filter(
        status='PENDING'
    ).aggregate(total=Sum('payment_amount'))['total'] or 0
    
    context = {
        'payments': payments,
        'status_choices': Payment.PAYMENT_STATUS,
        'method_choices': Payment.PAYMENT_METHODS,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'filters': {
            'status': status_filter,
            'method': method_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'finance/payment_list.html', context)


@login_required
def payment_create(request, invoice_id):
    """Create payment for invoice"""
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.user.role not in ['FINANCE', 'ADMIN']:
        messages.error(request, 'You do not have permission to create payments')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if invoice.status != 'APPROVED':
        messages.error(request, 'Invoice must be approved before payment')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                payment_date = request.POST.get('payment_date')
                payment_amount = Decimal(request.POST.get('payment_amount'))
                payment_method = request.POST.get('payment_method')
                payment_reference = request.POST.get('payment_reference')
                bank_name = request.POST.get('bank_name', '')
                cheque_number = request.POST.get('cheque_number', '')
                notes = request.POST.get('notes', '')
                
                # Validate amount
                total_paid = invoice.payments.filter(
                    status__in=['COMPLETED', 'PROCESSING']
                ).aggregate(total=Sum('payment_amount'))['total'] or 0
                
                if total_paid + payment_amount > invoice.total_amount:
                    messages.error(request, 'Payment amount exceeds invoice balance')
                    return redirect('payment_create', invoice_id=invoice_id)
                
                payment = Payment.objects.create(
                    invoice=invoice,
                    payment_date=payment_date,
                    payment_amount=payment_amount,
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    bank_name=bank_name,
                    cheque_number=cheque_number,
                    notes=notes,
                    processed_by=request.user,
                    status='PENDING'
                )
                
                messages.success(request, f'Payment {payment.payment_number} created successfully')
                return redirect('invoice_detail', invoice_id=invoice_id)
                
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
    
    # Calculate remaining balance
    total_paid = invoice.payments.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('payment_amount'))['total'] or 0
    
    remaining = invoice.total_amount - total_paid
    
    context = {
        'invoice': invoice,
        'remaining': remaining,
        'payment_methods': Payment.PAYMENT_METHODS,
    }
    
    return render(request, 'finance/payment_create.html', context)


@login_required
def payment_process(request, payment_id):
    """Process/complete payment"""
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.user.role not in ['FINANCE', 'ADMIN']:
        messages.error(request, 'You do not have permission to process payments')
        return redirect('payment_list')
    
    if payment.status != 'PENDING':
        messages.error(request, 'Payment has already been processed')
        return redirect('payment_list')
    
    if request.method == 'POST':
        payment.status = 'COMPLETED'
        payment.approved_by = request.user
        payment.save()
        
        # Update invoice status if fully paid
        total_paid = payment.invoice.payments.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('payment_amount'))['total'] or 0
        
        if total_paid >= payment.invoice.total_amount:
            payment.invoice.status = 'PAID'
            payment.invoice.payment_date = timezone.now().date()
            payment.invoice.save()
        
        messages.success(request, f'Payment {payment.payment_number} processed successfully')
        return redirect('payment_list')
    
    context = {'payment': payment}
    return render(request, 'finance/payment_process.html', context)


from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta, datetime
import json
from decimal import Decimal

@login_required
def financial_reports(request):
    """Financial reports dashboard with dynamic data and audit analytics"""
    
    # Get filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    budget_year_id = request.GET.get('budget_year')
    
    # Default to current year
    current_year = BudgetYear.objects.filter(is_active=True).first()
    
    if budget_year_id:
        selected_year = BudgetYear.objects.filter(id=budget_year_id).first()
    else:
        selected_year = current_year
    
    # Set date range
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = selected_year.start_date if selected_year else timezone.now().date().replace(month=1, day=1)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = selected_year.end_date if selected_year else timezone.now().date()
    
    # ============================================================================
    # 1. BUDGET UTILIZATION DATA
    # ============================================================================
    
    budget_summary = Budget.objects.filter(
        budget_year=selected_year
    ).aggregate(
        total_allocated=Sum('allocated_amount'),
        total_committed=Sum('committed_amount'),
        total_spent=Sum('actual_spent'),
        count=Count('id')
    )
    
    budget_utilization = []
    if budget_summary['total_allocated']:
        utilization_rate = (budget_summary['total_spent'] / budget_summary['total_allocated']) * 100
    else:
        utilization_rate = 0
    
    # Budget by department
    dept_budgets = Budget.objects.filter(
        budget_year=selected_year
    ).values(
        'department__name',
        'department__code'
    ).annotate(
        allocated=Sum('allocated_amount'),
        committed=Sum('committed_amount'),
        spent=Sum('actual_spent'),
        available=Sum('allocated_amount') - Sum('committed_amount') - Sum('actual_spent')
    ).order_by('-allocated')[:10]
    
    # Budget by category
    category_budgets = Budget.objects.filter(
        budget_year=selected_year
    ).values(
        'category__name',
        'category__code'
    ).annotate(
        allocated=Sum('allocated_amount'),
        spent=Sum('actual_spent'),
        utilization=ExpressionWrapper(
            Sum('actual_spent') * 100 / Sum('allocated_amount'),
            output_field=DecimalField()
        )
    ).order_by('-allocated')[:8]
    
    # ============================================================================
    # 2. EXPENDITURE ANALYSIS DATA
    # ============================================================================
    
    # Monthly expenditure trend
    monthly_expenditure = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        amount=Sum('payment_amount'),
        count=Count('id')
    ).order_by('month')
    
    # Expenditure by department
    dept_expenditure = Invoice.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status='PAID'
    ).values(
        'purchase_order__requisition__department__name'
    ).annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total')[:10]
    
    # Expenditure by category
    category_expenditure = InvoiceItem.objects.filter(
        invoice__created_at__gte=start_date,
        invoice__created_at__lte=end_date,
        invoice__status='PAID'
    ).values(
        'po_item__requisition_item__item__category__name'
    ).annotate(
        total=Sum('total_price'),
        count=Count('id')
    ).order_by('-total')[:10]
    
    # ============================================================================
    # 3. SUPPLIER PAYMENTS DATA
    # ============================================================================
    
    # Supplier payment summary
    supplier_payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).values(
        'invoice__supplier__name',
        'invoice__supplier__supplier_number'
    ).annotate(
        total=Sum('payment_amount'),
        count=Count('id'),
        avg_payment=Avg('payment_amount')
    ).order_by('-total')[:15]
    
    # Payment method distribution
    payment_methods = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).values('payment_method').annotate(
        total=Sum('payment_amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Supplier performance
    supplier_performance = SupplierPerformance.objects.filter(
        reviewed_at__gte=start_date,
        reviewed_at__lte=end_date
    ).values(
        'supplier__name'
    ).annotate(
        avg_rating=Avg('overall_rating'),
        count=Count('id')
    ).order_by('-avg_rating')[:10]
    
    # ============================================================================
    # 4. INVOICE AGING ANALYSIS
    # ============================================================================
    
    # Invoice aging buckets
    today = timezone.now().date()
    
    aging_data = []
    aging_buckets = [
        ('Current', 0, 30),
        ('31-60 days', 31, 60),
        ('61-90 days', 61, 90),
        ('Over 90 days', 91, 365),
    ]
    
    for bucket_name, min_days, max_days in aging_buckets:
        min_date = today - timedelta(days=max_days)
        max_date = today - timedelta(days=min_days) if min_days > 0 else today
        
        invoices = Invoice.objects.filter(
            created_at__range=[min_date, max_date],
            status__in=['SUBMITTED', 'VERIFYING', 'MATCHED', 'APPROVED']
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            avg_age=Avg(today - F('created_at'))
        )
        
        aging_data.append({
            'bucket': bucket_name,
            'total': invoices['total'] or 0,
            'count': invoices['count'] or 0,
            'avg_days': invoices['avg_age'].days if invoices['avg_age'] else 0
        })
    
    # Overdue invoices
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['SUBMITTED', 'VERIFYING', 'MATCHED', 'APPROVED']
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # ============================================================================
    # 5. CASH FLOW ANALYSIS
    # ============================================================================
    
    # Monthly cash flow
    monthly_cashflow = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i > 0:
            next_month = month_date.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        else:
            month_end = today
        
        # Cash in (allocations)
        cash_in = BudgetReallocation.objects.filter(
            status='APPROVED',
            approved_at__gte=month_start,
            approved_at__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Cash out (payments)
        cash_out = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end,
            status='COMPLETED'
        ).aggregate(total=Sum('payment_amount'))['total'] or 0
        
        monthly_cashflow.append({
            'month': month_start.strftime('%b %Y'),
            'cash_in': cash_in,
            'cash_out': cash_out,
            'net_flow': cash_in - cash_out
        })
    
    # ============================================================================
    # 6. AUDIT & COMPLIANCE DATA
    # ============================================================================
    
    # Audit trail summary
    audit_summary = AuditLog.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # High-value transactions
    high_value_payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED',
        payment_amount__gte=1000000  # Payments over 1M
    ).select_related(
        'invoice', 'invoice__supplier'
    ).order_by('-payment_amount')[:10]
    
    # Compliance checks
    compliance_data = {
        'three_way_matched': Invoice.objects.filter(
            is_three_way_matched=True,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count(),
        'unmatched_invoices': Invoice.objects.filter(
            is_three_way_matched=False,
            status='PAID',
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count(),
        'suppliers_with_expired_docs': Supplier.objects.filter(
            Q(tax_compliance_expiry__lt=today) | 
            Q(registration_expiry__lt=today),
            status='APPROVED'
        ).count(),
    }
    
    # ============================================================================
    # 7. PROCUREMENT PERFORMANCE
    # ============================================================================
    
    # Requisition to PO timeline
    timeline_data = PurchaseOrder.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        timeline=ExpressionWrapper(
            F('created_at') - F('requisition__created_at'),
            output_field=DurationField()
        )
    ).aggregate(
        avg_days=Avg('timeline'),
        min_days=Min('timeline'),
        max_days=Max('timeline')
    )
    
    # Tender success rate
    tender_stats = Tender.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total=Count('id'),
        awarded=Count('id', filter=Q(status='AWARDED')),
        cancelled=Count('id', filter=Q(status='CANCELLED'))
    )
    
    if tender_stats['total']:
        tender_success_rate = (tender_stats['awarded'] / tender_stats['total']) * 100
    else:
        tender_success_rate = 0
    
    # ============================================================================
    # 8. REPORT TYPES WITH DYNAMIC DATA
    # ============================================================================
    
    # Get all budget years for filter
    budget_years = BudgetYear.objects.all().order_by('-start_date')
    
    reports = {
        'budget_utilization': {
            'title': 'Budget Utilization Report',
            'description': f'Budget analysis for {selected_year.name if selected_year else "current year"}',
            'icon': 'chart-pie',
            'data_available': budget_summary['count'] > 0,
            'summary': {
                'allocated': budget_summary['total_allocated'] or 0,
                'spent': budget_summary['total_spent'] or 0,
                'utilization': utilization_rate
            }
        },
        'expenditure_analysis': {
            'title': 'Expenditure Analysis',
            'description': f'Expenditure breakdown from {start_date} to {end_date}',
            'icon': 'graph-up',
            'data_available': monthly_expenditure.count() > 0,
            'summary': {
                'total': Payment.objects.filter(
                    payment_date__gte=start_date,
                    payment_date__lte=end_date,
                    status='COMPLETED'
                ).aggregate(total=Sum('payment_amount'))['total'] or 0,
                'count': Payment.objects.filter(
                    payment_date__gte=start_date,
                    payment_date__lte=end_date,
                    status='COMPLETED'
                ).count()
            }
        },
        'supplier_payments': {
            'title': 'Supplier Payment Report',
            'description': f'Supplier payments from {start_date} to {end_date}',
            'icon': 'people',
            'data_available': supplier_payments.count() > 0,
            'summary': {
                'total_suppliers': supplier_payments.count(),
                'total_paid': sum(p['total'] for p in supplier_payments),
                'avg_per_supplier': sum(p['total'] for p in supplier_payments) / supplier_payments.count() if supplier_payments.count() > 0 else 0
            }
        },
        'invoice_aging': {
            'title': 'Invoice Aging Report',
            'description': 'Invoice status and aging analysis',
            'icon': 'clock-history',
            'data_available': aging_data and any(d['count'] > 0 for d in aging_data),
            'summary': {
                'overdue_total': overdue_invoices['total'] or 0,
                'overdue_count': overdue_invoices['count'] or 0,
                'current_count': aging_data[0]['count'] if aging_data else 0
            }
        },
        'cashflow': {
            'title': 'Cash Flow Report',
            'description': f'Monthly cash flow from {start_date} to {end_date}',
            'icon': 'currency-exchange',
            'data_available': len(monthly_cashflow) > 0,
            'summary': {
                'total_in': sum(c['cash_in'] for c in monthly_cashflow),
                'total_out': sum(c['cash_out'] for c in monthly_cashflow),
                'net_flow': sum(c['net_flow'] for c in monthly_cashflow)
            }
        },
        'audit_trail': {
            'title': 'Audit Trail Report',
            'description': f'System audit from {start_date} to {end_date}',
            'icon': 'shield-check',
            'data_available': audit_summary.count() > 0,
            'summary': {
                'total_actions': sum(a['count'] for a in audit_summary),
                'top_action': audit_summary[0]['action'] if audit_summary else 'None',
                'users_involved': AuditLog.objects.filter(
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).values('user').distinct().count()
            }
        },
        'compliance': {
            'title': 'Compliance Report',
            'description': 'Procurement compliance analysis',
            'icon': 'file-check',
            'data_available': True,
            'summary': {
                'matched_invoices': compliance_data['three_way_matched'],
                'unmatched_invoices': compliance_data['unmatched_invoices'],
                'suppliers_expired': compliance_data['suppliers_with_expired_docs']
            }
        },
        'performance': {
            'title': 'Procurement Performance',
            'description': 'System performance metrics',
            'icon': 'speedometer',
            'data_available': True,
            'summary': {
                'avg_timeline': timeline_data['avg_days'].days if timeline_data['avg_days'] else 0,
                'tender_success': tender_success_rate,
                'high_value_count': high_value_payments.count()
            }
        }
    }
    
    # Prepare chart data for JavaScript
    context = {
        'current_year': current_year,
        'selected_year': selected_year,
        'budget_years': budget_years,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
        
        # Report data
        'reports': reports,
        
        # Chart data for quick preview
        'chart_data': {
            # Budget Utilization Charts
            'budget_utilization': {
                'labels': [d['department__name'] for d in dept_budgets],
                'allocated': [float(d['allocated'] or 0) for d in dept_budgets],
                'spent': [float(d['spent'] or 0) for d in dept_budgets],
            },
            'category_budget': {
                'labels': [c['category__name'] for c in category_budgets],
                'allocated': [float(c['allocated'] or 0) for c in category_budgets],
                'utilization': [float(c['utilization'] or 0) for c in category_budgets],
            },
            
            # Expenditure Charts
            'monthly_expenditure': {
                'labels': [m['month'].strftime('%b %Y') for m in monthly_expenditure],
                'amounts': [float(m['amount'] or 0) for m in monthly_expenditure],
                'counts': [m['count'] for m in monthly_expenditure],
            },
            'dept_expenditure': {
                'labels': [d['purchase_order__requisition__department__name'] or 'Unknown' for d in dept_expenditure],
                'amounts': [float(d['total'] or 0) for d in dept_expenditure],
            },
            
            # Supplier Charts
            'supplier_payments': {
                'labels': [s['invoice__supplier__name'] for s in supplier_payments[:8]],
                'amounts': [float(s['total'] or 0) for s in supplier_payments[:8]],
            },
            'payment_methods': {
                'labels': [p['payment_method'] for p in payment_methods],
                'amounts': [float(p['total'] or 0) for p in payment_methods],
            },
            'supplier_performance': {
                'labels': [s['supplier__name'] for s in supplier_performance],
                'ratings': [float(s['avg_rating'] or 0) for s in supplier_performance],
            },
            
            # Invoice Aging Charts
            'invoice_aging': {
                'labels': [a['bucket'] for a in aging_data],
                'amounts': [float(a['total'] or 0) for a in aging_data],
                'counts': [a['count'] for a in aging_data],
            },
            
            # Cash Flow Charts
            'cash_flow': {
                'labels': [c['month'] for c in monthly_cashflow],
                'cash_in': [float(c['cash_in'] or 0) for c in monthly_cashflow],
                'cash_out': [float(c['cash_out'] or 0) for c in monthly_cashflow],
                'net_flow': [float(c['net_flow'] or 0) for c in monthly_cashflow],
            },
            
            # Audit Charts
            'audit_actions': {
                'labels': [a['action'] for a in audit_summary[:10]],
                'counts': [a['count'] for a in audit_summary[:10]],
            },
            
            # Compliance Charts
            'compliance_status': {
                'labels': ['3-Way Matched', 'Unmatched Paid', 'Suppliers Expired'],
                'values': [
                    compliance_data['three_way_matched'],
                    compliance_data['unmatched_invoices'],
                    compliance_data['suppliers_with_expired_docs']
                ],
            },
        },
        
        # Summary statistics for display
        'summary_stats': {
            'budget_allocated': budget_summary['total_allocated'] or 0,
            'budget_spent': budget_summary['total_spent'] or 0,
            'budget_utilization': round(utilization_rate, 2),
            'total_payments': Payment.objects.filter(
                payment_date__gte=start_date,
                payment_date__lte=end_date,
                status='COMPLETED'
            ).aggregate(total=Sum('payment_amount'))['total'] or 0,
            'total_invoices': Invoice.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count(),
            'total_suppliers': Supplier.objects.filter(status='APPROVED').count(),
            'overdue_invoices': overdue_invoices['count'] or 0,
            'overdue_amount': overdue_invoices['total'] or 0,
            'avg_supplier_rating': Supplier.objects.filter(
                status='APPROVED',
                rating__gt=0
            ).aggregate(avg=Avg('rating'))['avg'] or 0,
            'procurement_timeline': timeline_data['avg_days'].days if timeline_data['avg_days'] else 0,
        },
        
        # Table data for quick view
        'table_data': {
            'top_suppliers': list(supplier_payments[:5]),
            'high_value_payments': high_value_payments,
            'recent_audits': AuditLog.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).select_related('user').order_by('-timestamp')[:5],
            'department_budgets': list(dept_budgets[:5]),
        }
    }
    
    return render(request, 'finance/reports.html', context)

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

@login_required
def expenditure_report(request):
    """Detailed expenditure analysis with dynamic charts"""

    current_year = BudgetYear.objects.filter(is_active=True).first()

    # Date range filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().replace(month=1, day=1).date()

    if end_date:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    # =========================
    # Department Expenditure
    # =========================
    dept_expenditure = Budget.objects.filter(
        budget_year=current_year
    ).values('department__name').annotate(
        allocated=Sum('allocated_amount'),
        spent=Sum('actual_spent'),
        committed=Sum('committed_amount')
    ).order_by('-spent')[:10]

    # =========================
    # Category Expenditure
    # =========================
    category_expenditure = Budget.objects.filter(
        budget_year=current_year
    ).values('category__name').annotate(
        allocated=Sum('allocated_amount'),
        spent=Sum('actual_spent')
    ).order_by('-spent')[:8]

    # =========================
    # Monthly Expenditure Trend
    # =========================
    monthly_payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('payment_amount'),
        count=Count('id')
    ).order_by('month')

    # =========================
    # Payment Methods
    # =========================
    payment_methods = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).values('payment_method').annotate(
        total=Sum('payment_amount'),
        count=Count('id')
    ).order_by('-total')

    # =========================
    # Top Suppliers
    # =========================
    top_suppliers = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='COMPLETED'
    ).values('invoice__supplier__name').annotate(
        total=Sum('payment_amount'),
        count=Count('id')
    ).order_by('-total')[:10]

    # =========================
    # Budget Utilization
    # =========================
    budget_utilization = Budget.objects.filter(
        budget_year=current_year
    ).aggregate(
        total_allocated=Sum('allocated_amount'),
        total_spent=Sum('actual_spent'),
        total_committed=Sum('committed_amount')
    )

    utilization_rate = (
        (budget_utilization['total_spent'] / budget_utilization['total_allocated']) * 100
        if budget_utilization['total_allocated'] else 0
    )

    # =========================
    # Invoice Aging (FIXED)
    # =========================
    invoice_aging = Invoice.objects.filter(
        status__in=['SUBMITTED', 'VERIFYING', 'MATCHED', 'APPROVED']
    ).annotate(
        age=ExpressionWrapper(
            timezone.now().date() - F('created_at'),
            output_field=DurationField()
        )
    ).values('status').annotate(
        total_amount=Sum('total_amount'),
        count=Count('id'),
        avg_age=Avg('age')
    )

    # =========================
    # Payment Status Summary
    # =========================
    payment_status = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).values('status').annotate(
        total=Sum('payment_amount'),
        count=Count('id')
    )

    # =========================
    # Recent Payments
    # =========================
    recent_payments = Payment.objects.filter(
        status='COMPLETED'
    ).select_related(
        'invoice', 'invoice__supplier'
    ).order_by('-payment_date')[:10]

    # =========================
    # Context
    # =========================
    context = {
        'current_year': current_year,
        'start_date': start_date,
        'end_date': end_date,

        'monthly_chart': {
            'labels': [m['month'].strftime('%b %Y') for m in monthly_payments],
            'values': [float(m['total']) for m in monthly_payments],
            'counts': [m['count'] for m in monthly_payments],
        },

        'category_chart': {
            'labels': [c['category__name'] for c in category_expenditure],
            'values': [float(c['spent']) for c in category_expenditure],
            'allocated': [float(c['allocated']) for c in category_expenditure],
        },

        'dept_chart': {
            'labels': [d['department__name'] for d in dept_expenditure],
            'allocated': [float(d['allocated']) for d in dept_expenditure],
            'spent': [float(d['spent']) for d in dept_expenditure],
            'committed': [float(d['committed']) for d in dept_expenditure],
        },

        'payment_method_chart': {
            'labels': [p['payment_method'] for p in payment_methods],
            'values': [float(p['total']) for p in payment_methods],
            'counts': [p['count'] for p in payment_methods],
        },

        'supplier_chart': {
            'labels': [s['invoice__supplier__name'] for s in top_suppliers],
            'values': [float(s['total']) for s in top_suppliers],
            'counts': [s['count'] for s in top_suppliers],
        },

        'payment_status_chart': {
            'labels': [p['status'] for p in payment_status],
            'values': [float(p['total']) for p in payment_status],
            'counts': [p['count'] for p in payment_status],
        },

        'stats': {
            'total_allocated': budget_utilization['total_allocated'] or 0,
            'total_spent': budget_utilization['total_spent'] or 0,
            'total_committed': budget_utilization['total_committed'] or 0,
            'utilization_rate': round(utilization_rate, 2),
        },

        'recent_payments': recent_payments,
        'invoice_aging': invoice_aging,
        'category_expenditure': category_expenditure,
        'dept_expenditure': dept_expenditure,
    }

    return render(request, 'finance/expenditure_report.html', context)
