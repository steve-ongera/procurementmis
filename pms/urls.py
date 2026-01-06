from django.urls import path
from pms import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URL
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # Admin Analytics Dashboard
    path('admin-analytics/', views.admin_analytics_dashboard, name='admin_analytics_dashboard'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-reports/export/', views.export_report_excel, name='export_report_excel'),
    
    # Requisition Management
    path('requisitions/', views.requisition_list, name='requisition_list'),
    path('requisitions/create/', views.requisition_create, name='requisition_create'),
    path('requisitions/<uuid:pk>/', views.requisition_detail, name='requisition_detail'),
    path('requisitions/<uuid:pk>/update/', views.requisition_update, name='requisition_update'),
    path('requisitions/<uuid:pk>/delete/', views.requisition_delete, name='requisition_delete'),
    path('requisitions/<uuid:pk>/submit/', views.requisition_submit, name='requisition_submit'),
    path('requisitions/pending/', views.pending_requisitions, name='pending_requisitions'),
    
    # Approval Management Views
    path('approvals/pending/', views.pending_approvals, name='pending_approvals'),
    path('approvals/approved/', views.approved_requisitions, name='approved_requisitions'),
    path('approvals/rejected/', views.rejected_requisitions, name='rejected_requisitions'),
    path('approvals/<uuid:approval_id>/', views.approval_detail, name='approval_detail'),
    path('approvals/<uuid:approval_id>/process/', views.process_approval, name='process_approval'),
    path('approvals/bulk-approve/', views.bulk_approve, name='bulk_approve'),
    
    # API Endpoints
    path('api/approvals/stats/', views.api_approval_stats, name='api_approval_stats'),
    path('api/approvals/<uuid:approval_id>/', views.api_approval_details, name='api_approval_details'),
    path('api/requisitions/<uuid:requisition_id>/budget-check/', views.api_check_budget, name='api_check_budget'),
    
    # API Endpoints
    path('api/budget/<uuid:budget_id>/', views.get_budget_info, name='api_budget_info'),
    path('api/item/<uuid:item_id>/', views.get_item_info, name='api_item_info'),
    path('api/attachment/<uuid:attachment_id>/delete/', views.delete_attachment, name='api_delete_attachment'),
    
    # Tender Management
    path('tenders/', views.tender_list, name='tender_list'),
    path('tenders/create/', views.tender_create, name='tender_create'),
    path('tenders/<uuid:pk>/', views.tender_detail, name='tender_detail'),
     path('tenders/<uuid:tender_id>/edit/', views.edit_tender, name='tender_edit'),
    path('tenders/<uuid:pk>/publish/', views.tender_publish, name='tender_publish'),
    path('tenders/<uuid:pk>/close/', views.tender_close, name='tender_close'),
    path('tenders/<uuid:pk>/evaluate/', views.tender_evaluate, name='tender_evaluate'),
    path('tenders/<uuid:pk>/award/', views.tender_award, name='tender_award'),
    path('tenders/<uuid:pk>/cancel/', views.tender_cancel, name='tender_cancel'),
    
    # Bid Management
    path('tenders/<uuid:tender_id>/bids/', views.bid_list, name='bid_list'),
    path('bids/<uuid:pk>/', views.bid_detail, name='bid_detail'),
    
    # API Endpoints
    path('api/requisition/<uuid:requisition_id>/items/', views.get_requisition_items, name='api_requisition_items'),
    path('api/tenders/statistics/', views.get_tender_statistics, name='api_tender_statistics'),
    
    # Purchase Order URLs
    path('purchase-orders/dashboard/', views.po_dashboard, name='po_dashboard'),
    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/create/', views.po_create, name='po_create'),
    path('purchase-orders/<uuid:po_id>/', views.po_detail, name='po_detail'),
    path('purchase-orders/<uuid:po_id>/update/', views.po_update, name='po_update'),
    path('purchase-orders/<uuid:po_id>/approve/', views.po_approve, name='po_approve'),
    path('purchase-orders/<uuid:po_id>/send/', views.po_send, name='po_send'),
    path('purchase-orders/<uuid:po_id>/cancel/', views.po_cancel, name='po_cancel'),
    path('purchase-orders/<uuid:po_id>/amendment/create/', views.po_amendment_create, name='po_amendment_create'),
    
    # AJAX API Endpoints 
    path('api/requisition/<uuid:req_id>/details/', views.get_requisition_details, name='get_requisition_details'),
    path('api/requisition/<uuid:req_id>/supplier/<uuid:supplier_id>/bids/', views.get_supplier_bids, name='get_supplier_bids'),
    
     #Finance Dashboard
    path('finance/dashboard/', views.finance_dashboard, name='finance_dashboard'),
    
    # Budget Management
    path('finance/budgets/', views.budget_list, name='budget_list'),
    path('finance/budgets/create/', views.budget_create, name='budget_create'),
    path('finance/budgets/<uuid:budget_id>/', views.budget_detail, name='budget_detail'),
    path('finance/budgets/<uuid:budget_id>/reallocation/create/', 
         views.budget_reallocation_create, name='budget_reallocation_create'),
    
    # Invoice Management
    path('finance/invoices/', views.invoice_list, name='invoice_list'),
    path('finance/invoices/<uuid:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('finance/invoices/<uuid:invoice_id>/verify/', views.invoice_verify, name='invoice_verify'),
    path('finance/invoices/<uuid:invoice_id>/approve/', views.invoice_approve, name='invoice_approve'),
    
    # Payment Management
    path('finance/payments/', views.payment_list, name='payment_list'),
    path('finance/payments/create/<uuid:invoice_id>/', views.payment_create, name='payment_create'),
    path('finance/payments/<uuid:payment_id>/process/', views.payment_process, name='payment_process'),
    
    # Financial Reports
    path('finance/reports/', views.financial_reports, name='financial_reports'),
    path('finance/reports/expenditure/', views.expenditure_report, name='expenditure_report'),
    path('reports/budget-utilization/', views.budget_utilization_report, name='budget_utilization_report'),
    
    # Add other report URLs as needed
    # path('reports/expenditure/', views.expenditure_report, name='expenditure_report'),
    # path('reports/supplier-payments/', views.supplier_payments_report, name='supplier_payments_report'),
    # path('reports/invoice-aging/', views.invoice_aging_report, name='invoice_aging_report'),
    # path('reports/cashflow/', views.cashflow_report, name='cashflow_report'),
    # path('reports/audit-trail/', views.audit_trail_report, name='audit_trail_report'),
    # path('reports/compliance/', views.compliance_report, name='compliance_report'),
    # path('reports/performance/', views.performance_report, name='performance_report'),
    
    # Goods Received Notes
    path('grn/', views.grn_list, name='grn_list'),
    path('grn/<uuid:grn_id>/', views.grn_detail, name='grn_detail'),
    path('grn/create/', views.grn_create, name='grn_create'),
    path('grn/<uuid:grn_id>/inspect/', views.grn_inspect, name='grn_inspect'),
    
    # Stock Items
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/<uuid:stock_id>/', views.stock_detail, name='stock_detail'),
    path('stock/<uuid:stock_id>/adjustment/', views.stock_adjustment, name='stock_adjustment'),
    
    # Stock Issues
    path('issues/', views.issue_list, name='issue_list'),
    path('issues/create/', views.issue_create, name='issue_create'),
    path('issues/<uuid:issue_id>/', views.issue_detail, name='issue_detail'),
    path('issues/<uuid:issue_id>/process/', views.issue_process, name='issue_process'),
    
    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/<uuid:asset_id>/', views.asset_detail, name='asset_detail'),
    
    # API Endpoints
    path('inventory/api/stock-items/<uuid:store_id>/', views.get_stock_items_by_store, name='api_stock_items'),
    path('inventory/api/po-items/<uuid:po_id>/', views.get_po_items, name='api_po_items'),
    
    # ============================================================================
    # USER MANAGEMENT URLS
    # ============================================================================
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<uuid:user_id>/', views.user_detail, name='user_detail'),
    path('users/<uuid:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<uuid:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),

    path('roles-permissions/', views.role_permissions_list, name='role_permissions_list'),
    path('roles-permissions/<str:role_code>/edit/', views.role_permissions_edit, name='role_permissions_edit'),
    
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<uuid:dept_id>/', views.department_detail, name='department_detail'),
    
    #path('departments/<uuid:dept_id>/edit/', views.department_edit, name='department_edit'),
    path('settings/', views.system_settings, name='system_settings'),
    path('audit-trail/', views.audit_trail, name='audit_trail'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('policies/', views.policy_list, name='policy_list'),
    path('policies/<uuid:policy_id>/', views.policy_detail, name='policy_detail'),
    
    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<uuid:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<uuid:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<uuid:supplier_id>/update-status/', views.supplier_update_status, name='supplier_update_status'),
    path('suppliers/<uuid:supplier_id>/documents/', views.supplier_documents, name='supplier_documents'),
    path('suppliers/documents/<uuid:document_id>/verify/', views.supplier_verify_document, name='supplier_verify_document'),
    
    # Vendor Management URLs
    path('vendors/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendors/performance/', views.vendor_performance_list, name='vendor_performance_list'),
    path('vendors/performance/create/<uuid:po_id>/', views.vendor_performance_create, name='vendor_performance_create'),
    path('vendors/comparison/', views.vendor_comparison, name='vendor_comparison'),
    path('vendors/compliance/', views.vendor_compliance, name='vendor_compliance'),
    
    path('help-center/', views.help_center, name='help_center'),
    path('documentation/', views.documentation, name='documentation'),
    path('submit-ticket/', views.submit_support_ticket, name='submit_support_ticket'),
    
]