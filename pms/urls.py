from django.urls import path
from pms import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/supplier/', views.register_supplier, name='register_supplier'),
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
    path('requisitions/<uuid:pk>/approve/', views.requisition_approve, name='requisition_approve'),
    path('requisitions/<uuid:pk>/update/', views.requisition_update, name='requisition_update'),
    path('requisitions/<uuid:pk>/delete/', views.requisition_delete, name='requisition_delete'),
    path('requisitions/<uuid:pk>/submit/', views.requisition_submit, name='requisition_submit'),
    path('requisitions/pending/', views.pending_requisitions, name='pending_requisitions'),
    
    # Approval Management Views
    path('approvals/pending/', views.pending_approvals, name='pending_approvals'),
    path('approvals/approved/', views.approved_requisitions, name='approved_requisitions'),
    path('approvals/rejected/', views.rejected_requisitions, name='rejected_requisitions'),
    path('approvals/<uuid:approval_id>/', views.approval_detail, name='approval_detail'),
    #path('approvals/<uuid:approval_id>/process/', views.process_approval, name='process_approval'),
    
     path('approvals/<uuid:requisition_id>/process/', views.process_approval, name='process_approval'),
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
    
    # Evaluation Committee APIs
    path('api/tender/<uuid:tender_id>/committee/create/', views.create_evaluation_committee, name='api_create_committee'),
    path('api/committee/<uuid:committee_id>/add-member/', views.add_committee_member, name='api_add_committee_member'),
    path('api/committee/member/<uuid:member_id>/remove/', views.remove_committee_member,  name='api_remove_committee_member'),
    path('api/tender/<uuid:tender_id>/committee/members/', views.get_committee_members, name='api_get_committee_members'),
    path('api/committee/available-evaluators/', views.get_available_evaluators, name='api_available_evaluators'),
    path('api/committee/member/<uuid:member_id>/conflict/', views.update_committee_member_conflict, name='api_update_member_conflict'),
    
    # Bid Management
    path('bids/', views.bid_list, name='bid_list'),
    path('bids/<uuid:pk>/', views.bid_detail, name='bid_detail'),
    
    # Bid Evaluation URLs
    path('bids/<uuid:pk>/evaluate/technical/', views.bid_evaluate_technical, name='bid_evaluate_technical'),
    path('bids/<uuid:pk>/evaluate/financial/', views.bid_evaluate_financial, name='bid_evaluate_financial'),
    path('bids/<uuid:pk>/evaluation/view/', views.bid_view_evaluation, name='bid_view_evaluation'),
    
    # Committee URLs
    path('tenders/<uuid:tender_id>/committee/summary/', views.committee_evaluation_summary, name='committee_evaluation_summary'),
    
    # Bid Actions
    path('bids/<uuid:pk>/open/', views.bid_open, name='bid_open'),
    path('bids/<uuid:pk>/disqualify/', views.bid_disqualify, name='bid_disqualify'),
    path('bids/<uuid:pk>/award/', views.bid_award, name='bid_award'),
    
    # Comparison
    path('tenders/<uuid:tender_id>/bids/comparison/', views.bid_comparison, name='bid_comparison'),
    
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
    path('api/po/<uuid:po_id>/submit/', views.po_submit_for_approval, name='po_submit_for_approval'),
    
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
    
    # Invoice URLs
    path('grn/<uuid:grn_id>/create-invoice/', views.invoice_create, name='invoice_create'),
    path('invoice/<uuid:invoice_id>/submit/', views.invoice_submit, name='invoice_submit'),
    path('invoice/<uuid:invoice_id>/pay/', views.invoice_pay, name='invoice_pay'),
    
    # Payment URLs
    path('payment/<uuid:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payment/<uuid:payment_id>/complete/', views.payment_complete, name='payment_complete'),
    path('payment/<uuid:payment_id>/cancel/', views.payment_cancel, name='payment_cancel'),
    
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
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<uuid:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<uuid:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<uuid:supplier_id>/resend-credentials/', views.supplier_resend_credentials, name='supplier_resend_credentials'),
    
    path('suppliers/', views.supplier_list, name='supplier_list'),
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
    
    # Dashboard
    path('supplier/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),
    
    # Tenders & Opportunities
    path('supplier/tenders/', views.supplier_tenders_list, name='supplier_tenders_list'),
    path('supplier/tenders/<uuid:tender_id>/', views.supplier_tender_detail, name='supplier_tender_detail'),
    
    # Bids
    path('supplier/bids/', views.supplier_bids_list, name='supplier_bids_list'),
    path('supplier/bids/<uuid:bid_id>/', views.supplier_bid_detail, name='supplier_bid_detail'),
    path('supplier/tenders/<uuid:tender_id>/submit-bid/', views.supplier_submit_bid, name='supplier_submit_bid'),
    path('supplier/awarded-contracts/', views.supplier_awarded_contracts, name='supplier_awarded_contracts'),
    
    # Purchase Orders
    path('supplier/purchase-orders/', views.supplier_purchase_orders_list, name='supplier_purchase_orders_list'),
    path('supplier/purchase-orders/<uuid:po_id>/', views.supplier_purchase_order_detail, name='supplier_purchase_order_detail'),
    path('supplier/purchase-orders/<uuid:po_id>/acknowledge/', views.supplier_acknowledge_po, name='supplier_acknowledge_po'),
    path('supplier/pending-orders/', views.supplier_pending_orders, name='supplier_pending_orders'),
    path('supplier/deliveries/', views.supplier_deliveries, name='supplier_deliveries'),
    path('supplier/completed-orders/', views.supplier_completed_orders, name='supplier_completed_orders'),
    
    # Invoices & Payments
    path('supplier/invoices/', views.supplier_invoices_list, name='supplier_invoices_list'),
    path('supplier/invoices/<uuid:invoice_id>/', views.supplier_invoice_detail, name='supplier_invoice_detail'),
    path('supplier/invoices/submit/', views.supplier_submit_invoice, name='supplier_submit_invoice'),
    path('supplier/invoices/submit/<uuid:po_id>/', views.supplier_submit_invoice, name='supplier_submit_invoice_for_po'),
    path('supplier/payments/', views.supplier_payments, name='supplier_payments'),
    path('supplier/payment-history/', views.supplier_payment_history, name='supplier_payment_history'),
    # AJAX endpoint for getting PO details
    path('supplier/get-po-details/<uuid:po_id>/', views.get_po_details, name='get_po_details'),
    
    # Profile & Documents
    path('supplier/profile/', views.supplier_company_profile, name='supplier_company_profile'),
    path('supplier/documents/', views.supplier_documents, name='supplier_documents'),
    path('supplier/certifications/', views.supplier_certifications, name='supplier_certifications'),
    
    # Support
    path('supplier/help/', views.supplier_help_center, name='supplier_help_center'),
    path('supplier/contact-support/', views.supplier_contact_support, name='supplier_contact_support'),
    
    # staff Dashboard
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    # Requisitions Management
    path('staff/requisitions/', views.staff_requisitions_list, name='staff_requisitions_list'),
    path('staff/requisitions/new/', views.staff_requisition_create, name='staff_requisition_create'),
    path('staff/requisitions/<uuid:pk>/', views.staff_requisition_detail, name='staff_requisition_detail'),
    path('staff/requisitions/<uuid:pk>/edit/', views.staff_requisition_edit, name='staff_requisition_edit'),
    path('staff/requisitions/<uuid:pk>/submit/', views.staff_requisition_submit, name='staff_requisition_submit'),
    path('staff/requisitions/<uuid:pk>/cancel/', views.staff_requisition_cancel, name='staff_requisition_cancel'),
    path('api/search-items/' , views.api_search_items , name='api_search_items'),
    
    # Requisition Status Views
    path('staff/requisitions/pending/', views.staff_requisitions_pending, name='staff_requisitions_pending'),
    path('staff/requisitions/approved/', views.staff_requisitions_approved, name='staff_requisitions_approved'),
    path('staff/requisitions/rejected/', views.staff_requisitions_rejected, name='staff_requisitions_rejected'),
    
    # Help & Support
    path('staff/help/', views.staff_help_center, name='staff_help_center'),
    path('staff/guidelines/', views.staff_guidelines, name='staff_guidelines'),
    
    # ============================================================================
    # DASHBOARD & ANALYTICS
    # ============================================================================
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/analytics/', views.hod_analytics_view, name='hod_analytics'), 
    
    # ============================================================================
    # REQUISITIONS
    # ============================================================================
    path('hod/requisitions/my/', views.hod_my_requisitions_view, name='hod_my_requisitions'),
    path('hod/requisitions/new/', views.hod_new_requisition_view, name='hod_new_requisition'),
    path('hod/requisitions/department/', views.hod_department_requests_view, name='hod_department_requests'),
    path('hod/requisitions/<uuid:pk>/', views.hod_requisition_detail_view, name='hod_requisition_detail'),
    
    
    # ============================================================================
    # APPROVALS
    # ============================================================================
    path('hod/approvals/pending/', views.hod_pending_approvals_view, name='hod_pending_approvals'),
    path('hod/approvals/approved/', views.hod_approved_requisitions_view, name='hod_approved_requisitions'),
    path('hod/approvals/rejected/', views.hod_rejected_requisitions_view, name='hod_rejected_requisitions'),
    path('hod/approvals/history/', views.hod_approval_history_view, name='hod_approval_history'),
    
    # Approval actions
    path('hod/requisitions/<uuid:pk>/approve/', views.hod_approve_requisition_view, name='hod_approve_requisition'),
    path('hod/requisitions/<uuid:pk>/reject/', views.hod_reject_requisition_view, name='hod_reject_requisition'),
    
    # ============================================================================
    # DEPARTMENT MANAGEMENT
    # ============================================================================
    path('hod/budget/overview/', views.hod_budget_overview_view, name='hod_budget_overview'),
    path('hod/budget/expenditure/', views.hod_expenditure_reports_view, name='hod_expenditure_reports'),
    path('hod/staff/', views.hod_staff_management_view, name='hod_staff_management'),
    path('hod/staff/<uuid:user_id>/', views.hod_staff_detail_view, name='hod_staff_detail'),
    
    # ============================================================================
    # SUPPORT & HELP
    # ============================================================================
    path('hod/help/', views.hod_help_center_view, name='hod_help_center'),
    path('hod/guidelines/', views.hod_guidelines_view, name='hod_guidelines'),
    
    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    path('hod/api/quick-stats/', views.hod_quick_stats_api, name='hod_quick_stats_api'),
    path('hod/api/budget-check/', views.hod_budget_check_api, name='hod_budget_check_api'),
    path('hod/api/notifications/', views.hod_notifications_api, name='hod_notifications_api'),
    path('hod/api/notifications/<uuid:notification_id>/read/', views.hod_mark_notification_read_api, name='hod_mark_notification_read'),
    
    # ============================================================================
    # EXPORT/DOWNLOAD
    # ============================================================================
    path('hod/export/requisitions/csv/', views.hod_export_requisitions_csv, name='hod_export_requisitions_csv'),
    path('hod/export/budget/pdf/', views.hod_export_budget_pdf, name='hod_export_budget_pdf'),
    
    # Dashboard
    path('finance-module/dashboard/', views.finance_dashboard_view, name='finance_dashboard'),
    path('finance-module/analytics/', views.finance_analytics_view, name='finance_analytics'),
    
    # Budget Management
    path('finance-module/budgets/', views.finance_budgets_list_view, name='finance_budgets_list'),
    path('finance-module/budgets/<uuid:pk>/', views.finance_budget_detail_view, name='finance_budget_detail'),
    path('finance-module/budgets/create/', views.finance_budget_create_view, name='finance_budget_create'),
    path('finance-module/budgets/<uuid:pk>/edit/', views.finance_budget_edit_view, name='finance_budget_edit'),
    path('finance-module/budgets/allocation/', views.finance_budget_allocation_view, name='finance_budget_allocation'),
    path('finance-module/budgets/tracking/', views.finance_budget_tracking_view, name='finance_budget_tracking'),
    path('finance-module/budgets/reallocate/', views.finance_budget_reallocate_view, name='finance_budget_reallocate'),
    
    # Invoice Management
    path('finance-module/invoices/', views.finance_invoices_list_view, name='finance_invoices_list'),
    path('finance-module/invoices/<uuid:pk>/', views.finance_invoice_detail_view, name='finance_invoice_detail'),
    path('finance-module/invoices/<uuid:pk>/verify/', views.finance_invoice_verify_view, name='finance_invoice_verify'),
    path('finance-module/invoices/<uuid:pk>/approve/', views.finance_invoice_approve_view, name='finance_invoice_approve'),
    path('finance-module/invoices/pending/', views.finance_pending_invoices_view, name='finance_pending_invoices'),
    path('finance-module/invoices/paid/', views.finance_paid_invoices_view, name='finance_paid_invoices'),
    path('finance-module/invoices/overdue/', views.finance_overdue_invoices_view, name='finance_overdue_invoices'),
    
    # Payment Management
    path('finance-module/payments/', views.finance_payments_list_view, name='finance_payments_list'),
    path('finance-module/payments/<uuid:pk>/', views.finance_payment_detail_view, name='finance_payment_detail'),
    path('finance-module/payments/process/<uuid:invoice_id>/', views.finance_process_payment_view, name='finance_process_payment'),
    path('finance-module/payments/<uuid:pk>/approve/', views.finance_approve_payment_view, name='finance_approve_payment'),
    path('finance-module/payments/schedule/', views.finance_payment_schedule_view, name='finance_payment_schedule'),
    path('finance-module/payments/history/', views.finance_payment_history_view, name='finance_payment_history'),
    
    # Approvals
    path('finance-module/approvals/pending/', views.finance_pending_approvals_view, name='finance_pending_approvals'),
    path('finance-module/approvals/requisition/<uuid:requisition_id>/', views.finance_approve_requisition_view, name='finance_approve_requisition'),
    path('finance-module/approvals/approved/', views.finance_approved_requisitions_view, name='finance_approved_requisitions'),
    path('finance-module/approvals/rejected/', views.finance_rejected_requisitions_view, name='finance_rejected_requisitions'),
    
    # Reports
    path('finance-module/reports/expenditure/', views.finance_expenditure_report_view, name='finance_expenditure_report'),
    path('finance-module/reports/budget-vs-actual/', views.finance_budget_vs_actual_view, name='finance_budget_vs_actual'),
    path('finance-module/reports/financial-statements/', views.finance_financial_statements_view, name='finance_financial_statements'),
    path('finance-module/reports/transactions/', views.finance_transaction_report_view, name='finance_transaction_report'),
    path('finance-module/reports/export/', views.finance_export_report_view, name='finance_export_report'),
    
    # Help & Support
    path('finance-module/help/', views.finance_help_view, name='finance_help'),
    
    # ============================================================================
    # DASHBOARD & ANALYTICS
    # ============================================================================
    path('procurement-module/', views.procurement_dashboard_view, name='procurement_dashboard'),
    path('procurement-module/analytics/', views.procurement_analytics_view, name='procurement_analytics'),
    
    # ============================================================================
    # REQUISITIONS
    # ============================================================================
    path('procurement-module/requisitions/all/', views.procurement_all_requisitions_view, name='procurement_all_requisitions'),
    path('procurement-module/requisitions/pending/', views.procurement_pending_requisitions_view, name='procurement_pending_requisitions'),
    path('procurement-module/requisitions/processed/', views.procurement_processed_requisitions_view, name='procurement_processed_requisitions'),
    
    # ============================================================================
    # TENDERS
    # ============================================================================
    path('procurement-module/tenders/active/', views.procurement_active_tenders_view, name='procurement_active_tenders'),
    path('procurement-module/tenders/create/', views.procurement_create_tender_view, name='procurement_create_tender'),
    path('procurement-module/tenders/closed/', views.procurement_closed_tenders_view, name='procurement_closed_tenders'),
    path('procurement-module/tenders/evaluation/', views.procurement_tender_evaluation_view, name='procurement_tender_evaluation'),
    
    # ============================================================================
    # BIDS
    # ============================================================================
    path('procurement-module/bids/', views.procurement_bids_management_view, name='procurement_bids_management'),
    
    # ============================================================================
    # PURCHASE ORDERS
    # ============================================================================
    path('procurement-module/orders/all/', views.procurement_all_orders_view, name='procurement_all_orders'),
    path('procurement-module/orders/create/', views.procurement_create_order_view, name='procurement_create_order'),
    path('procurement-module/orders/pending/', views.procurement_pending_orders_view, name='procurement_pending_orders'),
    path('procurement-module/orders/completed/', views.procurement_completed_orders_view, name='procurement_completed_orders'),
    path('procurement-module/orders/<uuid:po_id>/', views.procurement_order_detail_view, name='procurement_order_detail'),
    path('po/<uuid:po_id>/download-pdf/', views.po_download_pdf, name='po_download_pdf'),
    
    # ============================================================================
    # CONTRACTS
    # ============================================================================
    path('procurement-module/contracts/', views.procurement_contracts_view, name='procurement_contracts'),
    
    # ============================================================================
    # SUPPLIERS
    # ============================================================================
    path('procurement-module/suppliers/all/', views.procurement_all_suppliers_view, name='procurement_all_suppliers'),
    path('procurement-module/suppliers/add/', views.procurement_add_supplier_view, name='procurement_add_supplier'),
    path('procurement-module/suppliers/evaluation/', views.procurement_supplier_evaluation_view, name='procurement_supplier_evaluation'),
    path('procurement-module/suppliers/blacklisted/', views.procurement_blacklisted_suppliers_view, name='procurement_blacklisted_suppliers'),
    
    # ============================================================================
    # REPORTS
    # ============================================================================
    path('procurement-module/reports/', views.procurement_reports_view, name='procurement_reports'),
    path('procurement-module/reports/spend-analysis/', views.procurement_spend_analysis_view, name='procurement_spend_analysis'),
    
    # ========================================================================
    # PROCUREMENT PLAN MANAGEMENT
    # ========================================================================
 
    # List & Detail
    path('plans/', views.procurement_plan_list, name='procurement_plan_list'),
    path('plans/<uuid:pk>/', views.procurement_plan_detail, name='procurement_plan_detail'),
    
    # Create & Edit
    path('plans/create/', views.procurement_plan_create, name='procurement_plan_create'),
    path('plans/<uuid:pk>/edit/', views.procurement_plan_edit, name='procurement_plan_edit'),
    # Workflow Actions
    path('plans/<uuid:pk>/submit/', views.procurement_plan_submit, name='procurement_plan_submit'),
    
    path('plans/<uuid:pk>/approve/', views.procurement_plan_approve, name='procurement_plan_approve'),
    
    path('plans/<uuid:pk>/reject/', views.procurement_plan_reject, name='procurement_plan_reject'),
    
    path('plans/<uuid:pk>/activate/', views.procurement_plan_activate, name='procurement_plan_activate'),
    
    # ========================================================================
    # PLAN ITEMS MANAGEMENT
    # ========================================================================
    
    # AJAX endpoints for plan items
    path('plans/<uuid:plan_pk>/items/add/', views.plan_item_add, name='plan_item_add'), 
    path('plans/items/<uuid:item_pk>/edit/', views.plan_item_edit, name='plan_item_edit'),
    path('plans/items/<uuid:item_pk>/delete/', views.plan_item_delete, name='plan_item_delete'),
    
    # ========================================================================
    # PLAN AMENDMENTS
    # ========================================================================
    
    # List & Create
    path('amendments/', views.plan_amendment_list, name='plan_amendment_list'),
    path('plans/<uuid:plan_pk>/amendments/create/', views.plan_amendment_create, name='plan_amendment_create'),
    
    # Approve & Reject
    path('amendments/<uuid:pk>/approve/', views.plan_amendment_approve, name='plan_amendment_approve'),
    path('amendments/<uuid:pk>/reject/', views.plan_amendment_reject, name='plan_amendment_reject'),
    
    # ========================================================================
    # REPORTS & ANALYTICS
    # ========================================================================
    
    # Reports
    path('plans/reports/', views.procurement_plan_reports, name='procurement_plan_reports'),

    # ========================================================================
    # UTILITY ENDPOINTS (AJAX)
    # ========================================================================
    
    # Get plan item details (for staff requisition form)
    path('api/plan-items/<uuid:plan_item_id>/details/', views.get_plan_item_details, name='get_plan_item_details'),
    
    # ============================================================================
    # GOODS RECEIPT URLs
    # ============================================================================
    path('goods-receipt/pending-deliveries/', views.store_pending_deliveries_view, name='store_pending_deliveries'),
    path('goods-receipt/receive-goods/', views.store_receive_goods_view, name='store_receive_goods'),
    path('goods-receipt/receive-goods/<uuid:po_id>/', views.store_receive_goods_view, name='store_receive_goods_po'),
    path('goods-receipt/history/', views.store_receipt_history_view, name='store_receipt_history'),
    path('goods-receipt/grn/<uuid:grn_id>/', views.store_grn_detail_view, name='store_grn_detail'),
    path('goods-receipt/quality-issues/', views.store_quality_issues_view, name='store_quality_issues'),
    
    # ============================================================================
    # STOCK MANAGEMENT URLs
    # ============================================================================
    path('inventory/all-stock/', views.store_all_stock_view, name='store_all_stock'),
    path('inventory/add-stock-item/', views.store_add_stock_item_view, name='store_add_stock_item'),
    path('inventory/low-stock-alert/', views.store_low_stock_alert_view, name='store_low_stock_alert'),
    path('inventory/out-of-stock/', views.store_out_of_stock_view, name='store_out_of_stock'),
    
    # ============================================================================
    # STOCK ISSUES URLs
    # ============================================================================
    path('issues/pending/', views.store_pending_issues_view, name='store_pending_issues'),
    path('issues/create/', views.store_issue_stock_view, name='store_create_issue'),
    path('issues/process/<uuid:issue_id>/', views.store_issue_stock_view, name='store_process_issue'),
    path('issues/history/', views.store_issue_history_view, name='store_issue_history'),
    path('issues/returns/', views.store_returns_view, name='store_returns'),
    
    # ============================================================================
    # OTHER STOCK OPERATIONS URLs
    # ============================================================================
    path('inventory/stock-takes/', views.store_stock_takes_view, name='store_stock_takes'),
    path('inventory/stock-transfers/', views.store_stock_transfers_view, name='store_stock_transfers'),
    
    # ============================================================================
    # ASSET MANAGEMENT URLs
    # ============================================================================
    path('assets/all/', views.store_all_assets_view, name='store_all_assets'),
    path('assets/register/', views.store_register_asset_view, name='store_register_asset'),
    path('assets/maintenance/', views.store_maintenance_view, name='store_maintenance'),
    path('assets/disposal/', views.store_disposal_view, name='store_disposal'),
    
    # ============================================================================
    # REPORTS URLs
    # ============================================================================
    path('reports/inventory/', views.store_inventory_reports_view, name='store_inventory_reports'),
    path('reports/movements/', views.store_movement_reports_view, name='store_movement_reports'),
    
    # ============================================================================
    # HELP & SUPPORT URL
    # ============================================================================
    path('help/', views.store_help_center_view, name='store_help_center'),
        
        
        
    # ============================================================================
    # AUDITOR MODULE URLS
    # ============================================================================

    # Dashboard & Analytics
    path('auditor/analytics/', views.auditor_analytics_view, name='auditor_analytics'),

    # Audit Management
    path('auditor/audits/all/', views.auditor_all_audits_view, name='auditor_all_audits'),
    path('auditor/audits/new/', views.auditor_new_audit_view, name='auditor_new_audit'),
    path('auditor/audits/active/', views.auditor_active_audits_view, name='auditor_active_audits'),
    path('auditor/audits/completed/', views.auditor_completed_audits_view, name='auditor_completed_audits'),

    # Transaction Reviews
    path('auditor/reviews/requisitions/', views.auditor_requisitions_review_view, name='auditor_requisitions_review'),
    path('auditor/reviews/purchase-orders/', views.auditor_purchase_orders_review_view, name='auditor_purchase_orders_review'),
    path('auditor/reviews/payments/', views.auditor_payments_review_view, name='auditor_payments_review'),
    path('auditor/reviews/contracts/', views.auditor_contracts_review_view, name='auditor_contracts_review'),

    # Compliance
    path('auditor/compliance/', views.auditor_compliance_review_view, name='auditor_compliance_review'),
    path('auditor/flagged-items/', views.auditor_flagged_items_view, name='auditor_flagged_items'),

    # System Audit
    path('auditor/system-audit/trail/', views.auditor_audit_trail_view, name='auditor_audit_trail'),
    path('auditor/system-audit/activity/', views.auditor_activity_logs_view, name='auditor_activity_logs'),
    path('auditor/system-audit/access/', views.auditor_access_logs_view, name='auditor_access_logs'),
    path('auditor/system-audit/data-changes/', views.auditor_data_changes_view, name='auditor_data_changes'),

    # Reports & Findings
    path('auditor/reports/audit-reports/', views.auditor_audit_reports_view, name='auditor_audit_reports'),
    path('auditor/reports/findings/', views.auditor_findings_view, name='auditor_findings'),
    path('auditor/reports/recommendations/', views.auditor_recommendations_view, name='auditor_recommendations'),
    path('auditor/reports/risk-assessment/', views.auditor_risk_assessment_view, name='auditor_risk_assessment'),

    # Help & Support
    path('auditor/help/', views.auditor_help_center_view, name='auditor_help_center'),
    # ============================================================================
    # PROFILE MANAGEMENT URLs
    # ============================================================================
    
    # Main profile router (checks role and redirects)
    path('profile/', views.profile_view, name='profile'),
    
    # Role-specific profile views
    path('profile/staff/', views.staff_profile, name='staff_profile'),
    path('profile/hod/', views.hod_profile, name='hod_profile'),
    path('profile/procurement/', views.procurement_profile, name='procurement_profile'),
    path('profile/finance/', views.finance_profile, name='finance_profile'),
    path('profile/stores/', views.stores_profile, name='stores_profile'),
    path('profile/supplier/', views.supplier_profile, name='supplier_profile'),
    path('profile/auditor/', views.auditor_profile, name='auditor_profile'),
    path('profile/admin/', views.admin_profile, name='admin_profile'),
    path('profile/generic/', views.generic_profile, name='generic_profile'),
    
    # Profile update
    path('profile/update/', views.profile_update, name='profile_update'),
    
    # Settings (you can create these later)
    path('settings/', views.user_settings, name='settings'),
    path('help/', views.help_center, name='help_center'),  # If not already added
   
    
]