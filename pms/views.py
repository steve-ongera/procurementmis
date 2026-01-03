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


def admin_dashboard(request):
    """Admin Dashboard"""
    context = {
        'total_users': User.objects.filter(is_active_user=True).count(),
        'total_requisitions': Requisition.objects.count(),
        'total_pos': PurchaseOrder.objects.count(),
        'total_suppliers': Supplier.objects.filter(status='APPROVED').count(),
        'pending_approvals': Requisition.objects.filter(
            status__in=['SUBMITTED', 'HOD_APPROVED', 'BUDGET_APPROVED']
        ).count(),
        'recent_activities': AuditLog.objects.all()[:10],
        'system_stats': {
            'departments': Department.objects.filter(is_active=True).count(),
            'active_contracts': Contract.objects.filter(status='ACTIVE').count(),
            'total_spend': Invoice.objects.filter(status='PAID').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0'),
        }
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
