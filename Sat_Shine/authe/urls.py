from django.urls import path
from . import views, dashboard_views, admin_views, travel_views, associate_views, enterprise_admin_views, enhanced_attendance_views, super_admin_views, bulk_upload_views, simple_redirect, test_views, debug_views, notification_views, reports_views
from django.shortcuts import redirect

def signup_redirect(request):
    return redirect('register')

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('signup/', signup_redirect, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('field-dashboard/', dashboard_views.field_dashboard, name='field_dashboard'),
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('associate-dashboard/', associate_views.associate_dashboard, name='associate_dashboard'),
    
    # Admin URLs
    path('admin/employees/', admin_views.employee_list, name='admin_employee_list'),
    path('admin/employees/<str:employee_id>/', admin_views.employee_detail, name='employee_detail'),
    path('admin/employees/<str:employee_id>/update/', admin_views.update_employee, name='update_employee'),
    path('admin/employees/<str:employee_id>/deactivate/', admin_views.deactivate_employee, name='deactivate_employee'),
    path('admin/employees/<str:employee_id>/activate/', admin_views.activate_employee, name='activate_employee'),
    path('admin/attendance/daily/', admin_views.attendance_daily, name='admin_attendance_daily'),
    path('admin/attendance/progress/', admin_views.attendance_progress, name='admin_attendance_progress'),
    path('admin/attendance/geo/', admin_views.attendance_geo, name='admin_attendance_geo'),
    path('admin/attendance/geo/data/', admin_views.attendance_geo_data, name='admin_attendance_geo_data'),
    path('admin/attendance/detailed/', admin_views.attendance_detailed, name='admin_attendance_detailed'),
    path('admin/attendance/update-status/', admin_views.update_attendance_status, name='update_attendance_status'),
    path('admin/employees/<str:employee_id>/attendance-history/', admin_views.employee_attendance_history, name='admin_employee_attendance_history'),
    path('admin/export/attendance-daily/', admin_views.export_attendance_daily, name='export_attendance_daily'),
    path('admin/leaves/', admin_views.leave_requests, name='admin_leave_requests'),
    path('admin/leaves/<int:leave_id>/decide/', admin_views.decide_leave, name='decide_leave'),
    path('admin/export/employees/', admin_views.export_employees, name='export_employees'),
    path('admin/export/travel-requests/', admin_views.export_travel_requests, name='export_travel_requests'),
    path('admin/todays-attendance/', admin_views.todays_attendance_details, name='todays_attendance_details'),
    path('admin/direct-approval/', admin_views.admin_direct_approval, name='admin_direct_approval'),
    
    # Approval System URLs
    path('admin/approval-status/', admin_views.approval_status, name='admin_approval_status'),
    path('admin/dc-confirmation/', admin_views.dc_confirmation, name='admin_dc_confirmation'),
    path('admin/admin-approval/', admin_views.admin_approval, name='admin_admin_approval'),
    path('admin/travel-approval/', admin_views.travel_approval, name='admin_travel_approval'),
    path('admin/bulk-approve-attendance/', admin_views.bulk_approve_attendance, name='bulk_approve_attendance'),
    
    # Field Officer URLs
    path('mark-attendance/', dashboard_views.mark_attendance, name='mark_attendance'),
    path('check-out/', dashboard_views.check_out, name='check_out'),
    path('attendance-history/', dashboard_views.attendance_history, name='attendance_history'),
    path('attendance/summary/', dashboard_views.attendance_summary, name='attendance_summary'),
    path('apply-leave/', dashboard_views.apply_leave, name='apply_leave'),
    path('confirm-team-attendance/', dashboard_views.confirm_team_attendance, name='confirm_team_attendance'),
    
    # Travel Request URLs
    path('travel-requests/', travel_views.travel_request_dashboard, name='travel_request_dashboard'),
    path('create-travel-request/', travel_views.create_travel_request, name='create_travel_request'),
    path('export-travel-requests/', travel_views.export_travel_requests, name='export_travel_requests'),
    path('get-associate-for-dccb/', travel_views.get_associate_for_dccb, name='get_associate_for_dccb'),
    
    # Associate URLs
    path('associate/mark-attendance/', associate_views.associate_mark_attendance, name='associate_mark_attendance'),
    path('associate/mark-attendance-page/', associate_views.associate_mark_attendance_page, name='associate_mark_attendance_page'),
    path('associate/attendance-status/', associate_views.get_attendance_status, name='associate_attendance_status'),
    path('associate/travel-approvals/', travel_views.associate_travel_approvals, name='associate_travel_approvals'),
    path('associate/approve-travel/<int:travel_id>/', travel_views.approve_travel_request, name='approve_travel_request'),
    path('travel-request-details/<int:request_id>/', associate_views.travel_request_details, name='travel_request_details'),
    path('auth/travel-request-details/<int:request_id>/', associate_views.travel_request_details, name='admin_travel_request_details'),
    
    # Enhanced attendance marking
    path('enhanced-mark-attendance/', enhanced_attendance_views.enhanced_mark_attendance, name='enhanced_mark_attendance'),
    
    # Super Admin URLs
    path('super-admin-dashboard/', super_admin_views.super_admin_dashboard, name='super_admin_dashboard'),
    path('employee-management/', simple_redirect.employee_management_redirect, name='employee_management'),
    path('create-user/', views.register_view, name='create_user'),
    
    # Bulk Upload URLs
    path('bulk-upload/', bulk_upload_views.bulk_upload_view, name='bulk_upload'),
    path('bulk-upload/preview/', bulk_upload_views.bulk_upload_preview, name='bulk_upload_preview'),
    path('download-template/', bulk_upload_views.download_template, name='download_template'),
    
    # Test URLs
    path('test-employees/', test_views.test_employee_list, name='test_employee_list'),
    
    # Debug URLs (Admin only)
    path('debug/travel-requests/', debug_views.debug_travel_requests, name='debug_travel_requests'),
    path('debug/create-sample-travel/', debug_views.create_sample_travel_request, name='create_sample_travel_request'),
    
    # AJAX validation endpoints
    path('validate-employee-id/', views.validate_employee_id, name='validate_employee_id'),
    path('validate-contact/', views.validate_contact, name='validate_contact'),
    path('validate-email/', views.validate_email, name='validate_email'),
    
    # Notification URLs
    path('notifications/', notification_views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', notification_views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Reports & Analytics URLs
    path('reports/', reports_views.reports_analytics_dashboard, name='reports_analytics_dashboard'),
    path('reports/attendance-analytics-api/', reports_views.attendance_analytics_api, name='attendance_analytics_api'),
    path('reports/attendance-trend-api/', reports_views.attendance_trend_api, name='attendance_trend_api'),
    path('reports/filtered-attendance-list/', reports_views.filtered_attendance_list, name='filtered_attendance_list'),
    path('reports/export-master-employee/', reports_views.export_master_employee_report, name='export_master_employee_report'),
    path('reports/export-master-attendance/', reports_views.export_master_attendance_report, name='export_master_attendance_report'),
]