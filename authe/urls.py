from django.urls import path
from . import views, dashboard_views, admin_views
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
    
    # Field Officer URLs
    path('mark-attendance/', dashboard_views.mark_attendance, name='mark_attendance'),
    path('attendance-history/', dashboard_views.attendance_history, name='attendance_history'),
    path('attendance/summary/', dashboard_views.attendance_summary, name='attendance_summary'),
    path('apply-leave/', dashboard_views.apply_leave, name='apply_leave'),
    
    # AJAX validation endpoints
    path('validate-employee-id/', views.validate_employee_id, name='validate_employee_id'),
    path('validate-contact/', views.validate_contact, name='validate_contact'),
    path('validate-email/', views.validate_email, name='validate_email'),
]