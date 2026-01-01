from django.urls import path
from . import views, dashboard_views, admin_views
from django.shortcuts import redirect

def signup_redirect(request):
    return redirect('register')

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('signup/', signup_redirect, name='signup'),  # Redirect old signup URL
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('field-dashboard/', dashboard_views.field_dashboard, name='field_dashboard'),
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Field Officer Attendance URLs
    path('mark-attendance/', dashboard_views.mark_attendance, name='mark_attendance'),
    path('attendance-history/', dashboard_views.attendance_history, name='attendance_history'),
    path('attendance/summary/', dashboard_views.attendance_summary, name='attendance_summary'),
    path('apply-leave/', dashboard_views.apply_leave, name='apply_leave'),
    path('team-attendance/', dashboard_views.team_attendance, name='team_attendance'),
    path('ping-employee/', dashboard_views.ping_employee, name='ping_employee'),
    
    # Admin URLs
    path('admin/employees/', admin_views.employee_list, name='admin_employee_list'),
    path('admin/employees/<str:employee_id>/', admin_views.employee_detail, name='admin_employee_detail'),
    path('admin/employees/<str:employee_id>/update/', admin_views.update_employee, name='admin_update_employee'),
    path('admin/employees/<str:employee_id>/deactivate/', admin_views.deactivate_employee, name='admin_deactivate_employee'),
    path('admin/attendance/daily/', admin_views.attendance_daily, name='admin_attendance_daily'),
    path('admin/attendance/progress/', admin_views.attendance_progress, name='admin_attendance_progress'),
    path('admin/attendance/geo/', admin_views.attendance_geo, name='admin_attendance_geo'),
    path('admin/attendance/geo-data/', admin_views.attendance_geo_data, name='admin_attendance_geo_data'),
    path('admin/leaves/', admin_views.leave_requests, name='admin_leave_requests'),
    path('admin/leaves/<int:leave_id>/decide/', admin_views.decide_leave, name='admin_decide_leave'),
    path('admin/export/employees/', admin_views.export_employees, name='export_employees'),
    path('admin/export/monthly-attendance/', admin_views.export_monthly_attendance, name='export_monthly_attendance'),
    path('admin/export/dccb-summary/', admin_views.export_dccb_summary, name='export_dccb_summary'),
    path('admin/export/date-range-attendance/', admin_views.export_date_range_attendance, name='export_date_range_attendance'),
    path('admin/reports-analytics/', admin_views.reports_analytics, name='admin_reports_analytics'),
    path('admin/analytics-data/', admin_views.analytics_data, name='analytics_data'),
    path('admin/compact-analytics-api/', admin_views.compact_analytics_api, name='compact_analytics_api'),
    path('admin/compact-analytics/', admin_views.compact_analytics_dashboard, name='admin_compact_analytics'),
    path('admin/employee/<str:employee_id>/attendance-history/', admin_views.employee_attendance_history, name='admin_employee_attendance_history'),
    
    # Notification URLs
    path('admin/notifications/', admin_views.notifications_api, name='admin_notifications_api'),
    path('admin/notifications/<int:notification_id>/read/', admin_views.mark_notification_read, name='mark_notification_read'),
    path('admin/notifications/mark-all-read/', admin_views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # AJAX validation endpoints
    path('validate-employee-id/', views.validate_employee_id, name='validate_employee_id'),
    path('validate-contact/', views.validate_contact, name='validate_contact'),
]