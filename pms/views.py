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
