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
]