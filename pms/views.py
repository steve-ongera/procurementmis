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