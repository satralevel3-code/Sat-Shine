from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField, F, Avg
from datetime import datetime, timedelta, time
from .models import CustomUser, Attendance, LeaveRequest, TravelRequest
from .admin_views import admin_required
import csv
import json
from math import radians, cos, sin, asin, sqrt

@login_required
@admin_required
def reports_analytics_dashboard(request):
    """Enhanced Reports & Analytics Dashboard with actionable cards"""
    today = timezone.localdate()
    
    # Get filter parameters
    date_filter = request.GET.get('date', today.isoformat())
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    department_filter = request.GET.get('department', '')
    
    try:
        selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
    
    # Base employee query
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    if department_filter:
        employees = employees.filter(department=department_filter)
    
    total_employees = employees.count()
    
    # Attendance Analytics for selected date
    attendance_today = Attendance.objects.filter(date=selected_date, user__in=employees)
    
    attendance_stats = {
        'present': attendance_today.filter(status='present').count(),
        'half_day': attendance_today.filter(status='half_day').count(),
        'absent': attendance_today.filter(status='absent').count(),
        'not_marked': total_employees - attendance_today.count(),
        'on_time': attendance_today.filter(check_in_time__lte=time(9, 30)).count(),
        'late': attendance_today.filter(check_in_time__gt=time(9, 30)).count(),
    }
    
    # Travel Analytics
    travel_stats = {
        'traveling': attendance_today.filter(travel_required=True).count(),
        'not_traveling': attendance_today.filter(travel_required=False).count(),
        'travel_approved': attendance_today.filter(travel_approved=True).count(),
    }
    
    # Approval Analytics
    approval_stats = {
        'dc_pending': attendance_today.filter(is_confirmed_by_dc=False).count(),
        'dc_confirmed': attendance_today.filter(is_confirmed_by_dc=True).count(),
        'admin_pending': attendance_today.filter(is_confirmed_by_dc=True, is_approved_by_admin=False).count(),
        'admin_approved': attendance_today.filter(is_approved_by_admin=True).count(),
    }
    
    # Leave Analytics - Enhanced
    leave_stats = {
        'pending_requests': LeaveRequest.objects.filter(status='pending').count(),
        'approved_today': LeaveRequest.objects.filter(
            status='approved',
            start_date__lte=selected_date,
            end_date__gte=selected_date
        ).count(),
        'on_leave_today': attendance_today.filter(is_leave_day=True).count(),
    }
    
    # Calculate percentages for better visualization
    attendance_percentage = 0
    punctuality_percentage = 0
    travel_percentage = 0
    leave_percentage = 0
    absenteeism_percentage = 0
    
    if total_employees > 0:
        attendance_percentage = round(((attendance_stats['present'] + attendance_stats['half_day'] * 0.5) / total_employees) * 100, 1)
        punctuality_percentage = round((attendance_stats['on_time'] / max(attendance_stats['present'] + attendance_stats['half_day'], 1)) * 100, 1)
        travel_percentage = round((travel_stats['traveling'] / total_employees) * 100, 1)
        leave_percentage = round((leave_stats['on_leave_today'] / total_employees) * 100, 1)
        absenteeism_percentage = round((attendance_stats['absent'] / total_employees) * 100, 1)
    
    context = {
        'selected_date': selected_date,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'department_filter': department_filter,
        'total_employees': total_employees,
        'attendance_stats': attendance_stats,
        'travel_stats': travel_stats,
        'approval_stats': approval_stats,
        'leave_stats': leave_stats,
        'attendance_percentage': attendance_percentage,
        'punctuality_percentage': punctuality_percentage,
        'travel_percentage': travel_percentage,
        'leave_percentage': leave_percentage,
        'absenteeism_percentage': absenteeism_percentage,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'department_choices': [('IT', 'IT'), ('HR', 'HR'), ('Finance', 'Finance'), ('Operations', 'Operations')],
    }
    
    return render(request, 'authe/reports_analytics_dashboard.html', context)

@login_required
@admin_required
def attendance_analytics_api(request):
    """API for attendance analytics charts"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    dccb_filter = request.GET.get('dccb', '')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    # Base query
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    attendance_records = Attendance.objects.filter(date=selected_date, user__in=employees)
    
    # Attendance Progress Data
    total_employees = employees.count()
    present_count = attendance_records.filter(status='present').count()
    half_day_count = attendance_records.filter(status='half_day').count()
    absent_count = attendance_records.filter(status='absent').count()
    not_marked_count = total_employees - attendance_records.count()
    
    attendance_progress = {
        'labels': ['Present', 'Half Day', 'Absent', 'Not Marked'],
        'data': [present_count, half_day_count, absent_count, not_marked_count],
        'colors': ['#059669', '#f59e0b', '#dc2626', '#6b7280']
    }
    
    # Travel Participation Data
    traveling_count = attendance_records.filter(travel_required=True).count()
    not_traveling_count = attendance_records.filter(travel_required=False).count()
    
    travel_participation = {
        'labels': ['Traveling', 'Not Traveling'],
        'data': [traveling_count, not_traveling_count],
        'colors': ['#2563eb', '#e5e7eb']
    }
    
    # Punctuality Data
    on_time_count = attendance_records.filter(check_in_time__lte=time(9, 30)).count()
    late_count = attendance_records.filter(check_in_time__gt=time(9, 30)).count()
    
    punctuality_data = {
        'labels': ['On Time', 'Late'],
        'data': [on_time_count, late_count],
        'colors': ['#059669', '#dc2626']
    }
    
    # Absenteeism Data
    absenteeism_data = {
        'labels': ['Present/Half Day', 'Absent'],
        'data': [present_count + half_day_count, absent_count],
        'colors': ['#059669', '#dc2626']
    }
    
    return JsonResponse({
        'attendance_progress': attendance_progress,
        'travel_participation': travel_participation,
        'punctuality_data': punctuality_data,
        'absenteeism_data': absenteeism_data,
        'selected_date': selected_date.isoformat()
    })

@login_required
@admin_required
def attendance_trend_api(request):
    """API for attendance trend chart (last 7 days)"""
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=6)
    
    dccb_filter = request.GET.get('dccb', '')
    
    # Base query
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    trend_data = []
    labels = []
    
    current_date = start_date
    while current_date <= end_date:
        attendance_day = Attendance.objects.filter(date=current_date, user__in=employees)
        
        day_stats = {
            'present': attendance_day.filter(status='present').count(),
            'half_day': attendance_day.filter(status='half_day').count(),
            'absent': attendance_day.filter(status='absent').count(),
            'on_time': attendance_day.filter(check_in_time__lte=time(9, 30)).count(),
            'late': attendance_day.filter(check_in_time__gt=time(9, 30)).count(),
        }
        
        trend_data.append(day_stats)
        labels.append(current_date.strftime('%m/%d'))
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'labels': labels,
        'datasets': [
            {
                'label': 'Present',
                'data': [day['present'] for day in trend_data],
                'borderColor': '#059669',
                'backgroundColor': 'rgba(5, 150, 105, 0.1)'
            },
            {
                'label': 'Absent',
                'data': [day['absent'] for day in trend_data],
                'borderColor': '#dc2626',
                'backgroundColor': 'rgba(220, 38, 38, 0.1)'
            },
            {
                'label': 'On Time',
                'data': [day['on_time'] for day in trend_data],
                'borderColor': '#2563eb',
                'backgroundColor': 'rgba(37, 99, 235, 0.1)'
            },
            {
                'label': 'Late',
                'data': [day['late'] for day in trend_data],
                'borderColor': '#f59e0b',
                'backgroundColor': 'rgba(245, 158, 11, 0.1)'
            }
        ]
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in KM"""
    if not all([lat1, lon1, lat2, lon2]):
        return 0
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return round(c * r, 2)

@login_required
@admin_required
def export_master_employee_report(request):
    """Enhanced Master Employee List Report"""
    # Apply filters
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    department_filter = request.GET.get('department', '')
    
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    if department_filter:
        employees = employees.filter(department=department_filter)
    
    employees = employees.order_by('employee_id')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="master_employee_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Enhanced Header
    writer.writerow([
        'EMP ID', 'Name', 'Designation', 'Department', 'Contact Number',
        'DCCB', 'Reporting Manager', 'Email ID', 'Date Joined', 'Status'
    ])
    
    # Data rows
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            employee.get_full_name(),
            employee.designation,
            employee.department or 'N/A',
            employee.contact_number,
            employee.dccb,
            'N/A',  # Reporting Manager - to be implemented
            employee.email,
            employee.date_joined.strftime('%Y-%m-%d'),
            'Active' if employee.is_active else 'Inactive'
        ])
    
    return response

@login_required
@admin_required
def export_master_attendance_report(request):
    """COMPREHENSIVE Master Attendance Report with ALL system data"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    dccb_filter = request.GET.get('dccb', '')
    employee_filter = request.GET.get('employee', '')
    
    if not start_date_str or not end_date_str:
        # Default to current month
        today = timezone.localdate()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get ALL attendance records in date range
    attendance_records = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('user', 'confirmed_by_dc', 'approved_by_admin').order_by('date', 'user__employee_id')
    
    # Apply filters
    if dccb_filter:
        attendance_records = attendance_records.filter(user__dccb=dccb_filter)
    if employee_filter:
        attendance_records = attendance_records.filter(user__employee_id__icontains=employee_filter)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="MPMT_Master_Attendance_Report_{start_date}_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # COMPREHENSIVE Header with ALL data fields
    writer.writerow([
        'Employee ID', 'Employee Name', 'Contact Number', 'Email', 'Designation', 
        'Department', 'DCCB', 'Reporting Manager', 'Date', 'Day of Week',
        'Check-In Time', 'Check-Out Time', 'Attendance Status', 'Time Status (On Time/Late)',
        'Working Hours', 'Break Hours', 'Overtime Hours', 'Location (Latitude)', 'Location (Longitude)',
        'Address/Workplace', 'Task Description', 'Travel Required (Y/N)', 'Travel Approved (Y/N)',
        'Travel Distance (KM)', 'Travel Purpose', 'Travel ER ID', 'Travel Contact Person',
        'DC Confirmation Status', 'DC Confirmed By', 'DC Confirmation Date', 'DC Confirmation Time',
        'Admin Approval Status', 'Admin Approved By', 'Admin Approval Date', 'Admin Approval Time',
        'Leave Status', 'Leave Type', 'Leave Reason', 'Leave Approved By',
        'Marked At (Date)', 'Marked At (Time)', 'Last Updated', 'Record Status',
        'GPS Accuracy', 'Device Info', 'IP Address', 'Remarks/Notes'
    ])
    
    # Process each attendance record
    for record in attendance_records:
        # Calculate working hours
        working_hours = 0
        break_hours = 0
        overtime_hours = 0
        
        if record.check_in_time and record.check_out_time:
            check_in_datetime = datetime.combine(record.date, record.check_in_time)
            check_out_datetime = datetime.combine(record.date, record.check_out_time)
            total_hours = (check_out_datetime - check_in_datetime).total_seconds() / 3600
            
            # Standard working hours calculation
            if total_hours > 8:
                working_hours = 8
                overtime_hours = round(total_hours - 8, 2)
            else:
                working_hours = round(total_hours, 2)
            
            # Assume 1 hour break for full day
            if total_hours > 4:
                break_hours = 1
        
        # Time status
        time_status = 'On Time'
        if record.check_in_time and record.check_in_time > time(9, 30):
            time_status = 'Late'
        elif not record.check_in_time:
            time_status = 'Not Marked'
        
        # Get travel request info for this date
        travel_request = TravelRequest.objects.filter(
            user=record.user,
            from_date__lte=record.date,
            to_date__gte=record.date
        ).first()
        
        # Get leave request info for this date
        leave_request = LeaveRequest.objects.filter(
            user=record.user,
            start_date__lte=record.date,
            end_date__gte=record.date
        ).first()
        
        # Day of week
        day_of_week = record.date.strftime('%A')
        
        # Record status
        record_status = 'Active'
        if not record.user.is_active:
            record_status = 'Inactive Employee'
        
        writer.writerow([
            record.user.employee_id,
            record.user.get_full_name(),
            record.user.contact_number or 'N/A',
            record.user.email or 'N/A',
            record.user.designation or 'N/A',
            record.user.department or 'N/A',
            record.user.dccb or 'N/A',
            record.user.reporting_manager or 'N/A',
            record.date.strftime('%Y-%m-%d'),
            day_of_week,
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else 'Not Marked',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else 'Not Marked',
            record.status.title(),
            time_status,
            working_hours,
            break_hours,
            overtime_hours,
            record.latitude or 'N/A',
            record.longitude or 'N/A',
            record.workplace or 'N/A',
            record.task or 'N/A',
            'Y' if record.travel_required else 'N',
            'Y' if record.travel_approved else 'N',
            travel_request.distance_km if travel_request else 'N/A',
            travel_request.purpose if travel_request else 'N/A',
            travel_request.er_id if travel_request else 'N/A',
            travel_request.contact_person if travel_request else 'N/A',
            'Confirmed' if record.is_confirmed_by_dc else 'Pending',
            record.confirmed_by_dc.employee_id if record.confirmed_by_dc else 'N/A',
            record.dc_confirmed_at.strftime('%Y-%m-%d') if record.dc_confirmed_at else 'N/A',
            record.dc_confirmed_at.strftime('%H:%M:%S') if record.dc_confirmed_at else 'N/A',
            'Approved' if record.is_approved_by_admin else 'Pending',
            record.approved_by_admin.employee_id if record.approved_by_admin else 'N/A',
            record.admin_approved_at.strftime('%Y-%m-%d') if record.admin_approved_at else 'N/A',
            record.admin_approved_at.strftime('%H:%M:%S') if record.admin_approved_at else 'N/A',
            'On Leave' if leave_request else 'Working',
            leave_request.leave_type if leave_request else 'N/A',
            leave_request.reason if leave_request else 'N/A',
            leave_request.approved_by.employee_id if leave_request and leave_request.approved_by else 'N/A',
            record.marked_at.strftime('%Y-%m-%d') if record.marked_at else 'N/A',
            record.marked_at.strftime('%H:%M:%S') if record.marked_at else 'N/A',
            record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(record, 'updated_at') and record.updated_at else 'N/A',
            record_status,
            'High' if record.latitude and record.longitude else 'N/A',  # GPS Accuracy placeholder
            'Mobile App',  # Device Info placeholder
            'N/A',  # IP Address placeholder
            record.remarks if hasattr(record, 'remarks') and record.remarks else 'N/A'
        ])
    
    return response

@login_required
@admin_required
def filtered_attendance_list(request):
    """API for filtered attendance list based on chart clicks"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    filter_type = request.GET.get('filter', '')  # present, absent, half_day, late, on_time, traveling
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    attendance_records = Attendance.objects.filter(date=selected_date).select_related('user')
    
    # Apply filters based on chart click
    if filter_type == 'present':
        attendance_records = attendance_records.filter(status='present')
    elif filter_type == 'absent':
        attendance_records = attendance_records.filter(status='absent')
    elif filter_type == 'half_day':
        attendance_records = attendance_records.filter(status='half_day')
    elif filter_type == 'late':
        attendance_records = attendance_records.filter(check_in_time__gt=time(9, 30))
    elif filter_type == 'on_time':
        attendance_records = attendance_records.filter(check_in_time__lte=time(9, 30))
    elif filter_type == 'traveling':
        attendance_records = attendance_records.filter(travel_required=True)
    
    data = []
    for record in attendance_records:
        data.append({
            'employee_id': record.user.employee_id,
            'name': record.user.get_full_name(),
            'dccb': record.user.dccb,
            'designation': record.user.designation,
            'status': record.status.title(),
            'check_in': record.check_in_time.strftime('%H:%M') if record.check_in_time else 'N/A',
            'check_out': record.check_out_time.strftime('%H:%M') if record.check_out_time else 'N/A',
            'travel': 'Yes' if record.travel_required else 'No',
            'workplace': record.workplace or 'N/A'
        })
    
    return JsonResponse({
        'data': data,
        'filter_type': filter_type,
        'date': selected_date.isoformat(),
        'count': len(data)
    })