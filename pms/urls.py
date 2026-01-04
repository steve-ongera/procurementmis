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
    
    # API Endpoints
    path('api/budget/<uuid:budget_id>/', views.get_budget_info, name='api_budget_info'),
    path('api/item/<uuid:item_id>/', views.get_item_info, name='api_item_info'),
    path('api/attachment/<uuid:attachment_id>/delete/', views.delete_attachment, name='api_delete_attachment'),
]