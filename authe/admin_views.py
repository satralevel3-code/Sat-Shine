from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date, time
from .models import CustomUser, Attendance, LeaveRequest, AuditLog
from .views import create_audit_log
import json
import csv
from io import StringIO
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

def admin_required(view_func):
    """Decorator to ensure only admin users can access admin views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Access denied. Please login.')
            return redirect('login')
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard with KPIs"""
    # Clear all messages on dashboard load to prevent persistence
    storage = messages.get_messages(request)
    storage.used = True
    
    today = timezone.localdate()
    
    # Total Employees KPI
    total_employees = CustomUser.objects.filter(role='field_officer').count()
    active_employees = CustomUser.objects.filter(role='field_officer', is_active=True).count()
    
    # Designation-wise count
    designation_counts = CustomUser.objects.filter(role='field_officer').values('designation').annotate(
        count=Count('id')
    ).order_by('designation')
    
    # DCCB-wise count
    dccb_counts = CustomUser.objects.filter(role='field_officer').exclude(dccb__isnull=True).values('dccb').annotate(
        count=Count('id')
    ).order_by('dccb')
    
    # Attendance KPIs for today
    attendance_kpis = Attendance.objects.filter(date=today).aggregate(
        present=Count(Case(When(status='present', then=1), output_field=IntegerField())),
        absent=Count(Case(When(status='absent', then=1), output_field=IntegerField())),
        half_day=Count(Case(When(status='half_day', then=1), output_field=IntegerField()))
    )
    
    # Calculate late arrivals (present after 9:30 AM)
    late_cutoff = time(9, 30)
    late_arrivals = Attendance.objects.filter(
        date=today,
        status='present',
        check_in_time__gt=late_cutoff
    ).count()
    attendance_kpis['late_arrivals'] = late_arrivals
    
    # Calculate not marked
    marked_today = Attendance.objects.filter(date=today).count()
    not_marked = active_employees - marked_today
    attendance_kpis['not_marked'] = not_marked
    
    # Attendance marking progress
    progress_percentage = (marked_today / active_employees * 100) if active_employees > 0 else 0
    
    # Pending leave requests
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'designation_counts': designation_counts,
        'dccb_counts': dccb_counts,
        'attendance_kpis': attendance_kpis,
        'progress_percentage': round(progress_percentage, 1),
        'pending_leaves': pending_leaves,
        'today': today,
    }
    
    return render(request, 'authe/admin_dashboard.html', context)

@login_required
@admin_required
def employee_list(request):
    """Employee master list with filters and pagination"""
    employees = CustomUser.objects.filter(role='field_officer').select_related()
    
    # Apply filters
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    dccb_filter = request.GET.get('dccb', '')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    designation_filter = request.GET.get('designation', '')
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(employees, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'status_choices': [('active', 'Active'), ('inactive', 'Inactive')],
    }
    
    return render(request, 'authe/admin_employee_list.html', context)

@login_required
@admin_required
@require_http_methods(["PUT"])
def update_employee(request, employee_id):
    """Update employee details"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    try:
        data = json.loads(request.body)
        
        # Store before data for audit
        before_data = f"Name: {employee.first_name} {employee.last_name}, Designation: {employee.designation}, DCCB: {employee.dccb}, Contact: {employee.contact_number}, Email: {employee.email}, Manager: {employee.reporting_manager}"
        
        # Update allowed fields
        if 'first_name' in data:
            employee.first_name = data['first_name'].upper()
        if 'last_name' in data:
            employee.last_name = data['last_name'].upper()
        if 'designation' in data:
            employee.designation = data['designation']
        if 'dccb' in data:
            employee.dccb = data['dccb'] if data['dccb'] else None
        if 'contact_number' in data:
            employee.contact_number = data['contact_number']
        if 'email' in data:
            employee.email = data['email']
        if 'reporting_manager' in data:
            employee.reporting_manager = data['reporting_manager'].upper() if data['reporting_manager'] else None
        
        with transaction.atomic():
            employee.save()
            
            # Create audit log
            after_data = f"Name: {employee.first_name} {employee.last_name}, Designation: {employee.designation}, DCCB: {employee.dccb}, Contact: {employee.contact_number}, Email: {employee.email}, Manager: {employee.reporting_manager}"
            
            create_audit_log(
                request.user,
                f'Employee Updated: {employee.employee_id}',
                request,
                f'Before: {before_data}, After: {after_data}'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Employee updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
@require_http_methods(["PATCH"])
def deactivate_employee(request, employee_id):
    """Deactivate employee account"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    # Protect demo users from deactivation
    if getattr(employee, 'is_demo_user', False):
        return JsonResponse({
            'success': False, 
            'error': 'Demo users cannot be deactivated. These are protected system accounts.'
        }, status=403)
    
    if not employee.is_active:
        return JsonResponse({'success': False, 'error': 'Employee already inactive'}, status=400)
    
    try:
        with transaction.atomic():
            # Store before data
            before_data = f"Status: {'Active' if employee.is_active else 'Inactive'}"
            
            # Deactivate employee
            employee.is_active = False
            employee.save()
            
            # Create audit log
            after_data = f"Status: {'Active' if employee.is_active else 'Inactive'}"
            create_audit_log(
                request.user,
                f'Employee Deactivated: {employee.employee_id}',
                request,
                f'Before: {before_data}, After: {after_data}'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Employee {employee.employee_id} has been deactivated'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def attendance_daily(request):
    """Daily attendance matrix view with month-based navigation"""
    from datetime import datetime, timedelta
    from .models import Holiday
    
    # Get date range (default: current month)
    today = timezone.localdate()
    
    # Default to current month if no dates provided
    default_from = today.replace(day=1)  # First day of current month
    default_to = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)  # Last day of current month
    
    from_date_str = request.GET.get('from_date', default_from.isoformat())
    to_date_str = request.GET.get('to_date', default_to.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = default_from
        to_date = default_to
    
    # Apply filters
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Debug: Print filter values
    print(f"DEBUG - DCCB Filter: '{dccb_filter}', Designation Filter: '{designation_filter}'")
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    print(f"DEBUG - Total active employees before filters: {employees.count()}")
    
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
        print(f"DEBUG - Employees after DCCB filter '{dccb_filter}': {employees.count()}")
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
        print(f"DEBUG - Employees after designation filter '{designation_filter}': {employees.count()}")
    
    # Generate date range
    date_range = []
    current_date = from_date
    holidays = Holiday.objects.filter(date__range=[from_date, to_date])
    holiday_dates = {h.date: h for h in holidays}
    
    while current_date <= to_date:
        is_sunday = current_date.weekday() == 6
        is_holiday = current_date in holiday_dates or is_sunday
        
        date_range.append({
            'date': current_date,
            'is_sunday': is_sunday,
            'is_holiday': is_holiday,
            'holiday_name': holiday_dates.get(current_date, {}).get('name', 'Sunday') if is_holiday else None
        })
        current_date += timedelta(days=1)
    
    # Get attendance data
    attendance_records = Attendance.objects.filter(
        date__range=[from_date, to_date],
        user__in=employees
    ).select_related('user')
    
    # Organize attendance by employee and date
    attendance_dict = {}
    for record in attendance_records:
        if record.user.employee_id not in attendance_dict:
            attendance_dict[record.user.employee_id] = {}
        
        # Check if late (after 9:30 AM)
        is_late = False
        if record.check_in_time and record.check_in_time > time(9, 30):
            is_late = True
        
        attendance_dict[record.user.employee_id][record.date] = {
            'status': record.status,
            'is_late': is_late,
            'check_in_time': record.check_in_time
        }
    
    # Prepare final data structure
    attendance_data = []
    for employee in employees:
        employee_attendance = []
        
        for date_info in date_range:
            date_obj = date_info['date']
            attendance = attendance_dict.get(employee.employee_id, {}).get(date_obj, {})
            
            employee_attendance.append({
                'date': date_obj,
                'status': attendance.get('status', 'not_marked'),
                'is_late': attendance.get('is_late', False),
                'is_sunday': date_info['is_sunday'],
                'is_holiday': date_info['is_holiday']
            })
        
        attendance_data.append({
            'employee': employee,
            'attendance_list': employee_attendance
        })
    
    context = {
        'attendance_data': attendance_data,
        'date_range': date_range,
        'from_date': from_date,
        'to_date': to_date,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
    }
    
    return render(request, 'authe/admin_attendance_daily.html', context)

@login_required
@admin_required
def attendance_progress(request):
    """Get real-time attendance marking progress"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    active_employees = CustomUser.objects.filter(role='field_officer', is_active=True).count()
    marked_today = Attendance.objects.filter(date=selected_date).count()
    
    progress_percentage = (marked_today / active_employees * 100) if active_employees > 0 else 0
    
    return JsonResponse({
        'total_employees': active_employees,
        'marked_employees': marked_today,
        'progress_percentage': round(progress_percentage, 1),
        'date': selected_date.isoformat()
    })

@login_required
@admin_required
def leave_requests(request):
    """Leave approval workflow - show all records, filter on client side"""
    # Get all leave requests (no server-side filtering)
    leaves = LeaveRequest.objects.select_related('user').order_by('-applied_at')
    
    # Pagination
    paginator = Paginator(leaves, 50)  # Increased to 50 for better client-side filtering
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    }
    
    return render(request, 'authe/admin_leave_requests.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def decide_leave(request, leave_id):
    """Approve or reject leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    
    if leave_request.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Leave request already processed'}, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'reject'
        admin_remarks = data.get('admin_remarks', '')
        
        if action not in ['approve', 'reject']:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        with transaction.atomic():
            # Store before data
            before_data = f"Status: {leave_request.status}"
            
            # Update leave request
            leave_request.status = 'approved' if action == 'approve' else 'rejected'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.admin_remarks = admin_remarks
            leave_request.save()
            
            # Create audit log
            after_data = f"Status: {leave_request.status}"
            create_audit_log(
                request.user,
                f'Leave Request {action.title()}d: {leave_request.id}',
                request,
                f'Before: {before_data}, After: {after_data}'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Leave request {action}d successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def compact_analytics(request):
    """Compact analytics dashboard with 4 charts in 2x2 grid"""
    today = timezone.localdate()
    
    # Get attendance data for today
    attendance_today = Attendance.objects.filter(date=today)
    total_employees = CustomUser.objects.filter(role='field_officer', is_active=True).count()
    
    # 1. Attendance Status Distribution
    status_counts = attendance_today.aggregate(
        present=Count(Case(When(status='present', then=1), output_field=IntegerField())),
        absent=Count(Case(When(status='absent', then=1), output_field=IntegerField())),
        half_day=Count(Case(When(status='half_day', then=1), output_field=IntegerField()))
    )
    not_marked = total_employees - sum(status_counts.values())
    attendance_percentage = round((status_counts['present'] + status_counts['half_day'] * 0.5) / total_employees * 100, 1) if total_employees > 0 else 0
    
    # 2. Late Arrival Distribution
    late_cutoff = time(9, 30)
    on_time = attendance_today.filter(status__in=['present', 'half_day'], check_in_time__lte=late_cutoff).count()
    late = attendance_today.filter(status__in=['present', 'half_day'], check_in_time__gt=late_cutoff).count()
    
    # 3. DCCB Attendance Comparison (top 6 DCCBs)
    dccb_stats = []
    dccb_attendance = CustomUser.objects.filter(role='field_officer', is_active=True, dccb__isnull=False).values('dccb').annotate(
        total=Count('id'),
        present_today=Count(Case(When(attendance__date=today, attendance__status__in=['present', 'half_day'], then=1), output_field=IntegerField()))
    ).order_by('-total')[:6]
    
    for dccb in dccb_attendance:
        percentage = round(dccb['present_today'] / dccb['total'] * 100, 1) if dccb['total'] > 0 else 0
        dccb_stats.append({
            'name': dccb['dccb'],
            'percentage': percentage,
            'present': dccb['present_today'],
            'total': dccb['total']
        })
    
    # 4. Attendance Trend (last 7 days)
    trend_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_attendance = Attendance.objects.filter(date=date)
        day_total = CustomUser.objects.filter(role='field_officer', is_active=True).count()
        
        present_count = day_attendance.filter(status__in=['present', 'half_day']).count()
        absent_count = day_attendance.filter(status='absent').count()
        
        present_pct = round(present_count / day_total * 100, 1) if day_total > 0 else 0
        absent_pct = round(absent_count / day_total * 100, 1) if day_total > 0 else 0
        
        trend_data.append({
            'date': date.strftime('%m/%d'),
            'present_pct': present_pct,
            'absent_pct': absent_pct
        })
    
    context = {
        'attendance_status': {
            'present': status_counts['present'],
            'absent': status_counts['absent'],
            'half_day': status_counts['half_day'],
            'not_marked': not_marked,
            'percentage': attendance_percentage
        },
        'late_arrival': {
            'on_time': on_time,
            'late': late,
            'total': on_time + late
        },
        'dccb_stats': dccb_stats,
        'trend_data': trend_data,
        'today': today
    }
    
    return render(request, 'authe/admin_compact_analytics.html', context)

@login_required
@admin_required
def attendance_geo(request):
    """Attendance geo-location view with map"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    context = {
        'selected_date': selected_date,
    }
    
    return render(request, 'authe/admin_attendance_geo_working.html', context)

@login_required
@admin_required
def attendance_geo_data(request):
    """API endpoint for map loading with lat/lng fields"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    status_filter = request.GET.get('status', '')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    # Query with lat/lng fields
    attendance_query = Attendance.objects.filter(
        date=selected_date,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('user').only(
        'user__employee_id', 'user__first_name', 'user__last_name', 
        'user__designation', 'user__dccb', 'status', 'check_in_time',
        'latitude', 'longitude', 'location_accuracy', 'location_address',
        'distance_from_office', 'is_location_valid', 'marked_at'
    )
    
    # Apply status filter if provided
    if status_filter:
        attendance_query = attendance_query.filter(status=status_filter)
    
    # Process records efficiently
    geo_data = []
    for record in attendance_query:
        lat = float(record.latitude)
        lng = float(record.longitude)
        
        geo_data.append({
            'employee_id': record.user.employee_id,
            'name': f"{record.user.first_name} {record.user.last_name}",
            'designation': record.user.designation,
            'dccb': record.user.dccb or '',
            'status': record.status,
            'is_late': record.check_in_time > time(10, 0) if record.check_in_time else False,
            'timing_status': 'On Time' if record.check_in_time and record.check_in_time <= time(10, 0) else 'Late' if record.check_in_time else 'Not Marked',
            'lat': round(lat, 8),
            'lng': round(lng, 8),
            'marked_at': record.marked_at.strftime('%H:%M') if record.marked_at else '',
            'check_in_time': record.check_in_time.strftime('%H:%M') if record.check_in_time else '',
            'location_address': record.location_address or f'GPS Location ({lat:.6f}, {lng:.6f})',
            'location_accuracy': round(record.location_accuracy) if record.location_accuracy else 0,
            'distance_from_office': round(record.distance_from_office) if record.distance_from_office else 0,
            'is_location_valid': record.is_location_valid
        })
    
    return JsonResponse(geo_data, safe=False)

@login_required
@admin_required
def attendance_detailed(request):
    """Detailed attendance view with scrollable table"""
    from datetime import datetime, timedelta
    from .models import Holiday
    
    # Get date range (default: current month)
    today = timezone.localdate()
    from_date_str = request.GET.get('from_date', today.replace(day=1).isoformat())
    to_date_str = request.GET.get('to_date', today.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = today.replace(day=1)
        to_date = today
    
    # Apply filters
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Generate date range
    date_range = []
    current_date = from_date
    holidays = Holiday.objects.filter(date__range=[from_date, to_date])
    holiday_dates = {h.date: h for h in holidays}
    
    while current_date <= to_date:
        is_sunday = current_date.weekday() == 6
        is_holiday = current_date in holiday_dates or is_sunday
        
        date_range.append({
            'date': current_date,
            'is_sunday': is_sunday,
            'is_holiday': is_holiday,
            'holiday_name': holiday_dates.get(current_date, {}).get('name', 'Sunday') if is_holiday else None
        })
        current_date += timedelta(days=1)
    
    # Get attendance data
    attendance_records = Attendance.objects.filter(
        date__range=[from_date, to_date],
        user__in=employees
    ).select_related('user')
    
    # Organize attendance by employee and date
    attendance_dict = {}
    for record in attendance_records:
        if record.user.employee_id not in attendance_dict:
            attendance_dict[record.user.employee_id] = {}
        
        # Check if late (after 9:30 AM)
        is_late = False
        if record.check_in_time and record.check_in_time > time(9, 30):
            is_late = True
        
        attendance_dict[record.user.employee_id][record.date] = {
            'status': record.status,
            'is_late': is_late,
            'check_in_time': record.check_in_time
        }
    
    # Prepare final data structure
    attendance_data = []
    for employee in employees:
        employee_attendance = []
        
        for date_info in date_range:
            date_obj = date_info['date']
            attendance = attendance_dict.get(employee.employee_id, {}).get(date_obj, {})
            
            employee_attendance.append({
                'date': date_obj,
                'status': attendance.get('status', 'not_marked'),
                'is_late': attendance.get('is_late', False),
                'is_sunday': date_info['is_sunday'],
                'is_holiday': date_info['is_holiday']
            })
        
        attendance_data.append({
            'employee': employee,
            'attendance_list': employee_attendance
        })
    
    context = {
        'attendance_data': attendance_data,
        'date_range': date_range,
        'from_date': from_date.isoformat(),
        'to_date': to_date.isoformat(),
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
    }
    
    return render(request, 'authe/admin_attendance_detailed.html', context)

@login_required
@admin_required
def export_attendance_detailed(request):
    """Export detailed attendance data"""
    format_type = request.GET.get('format', 'csv')
    
    # Get same data as detailed view
    from datetime import datetime, timedelta
    from .models import Holiday
    
    today = timezone.localdate()
    from_date_str = request.GET.get('from_date', today.replace(day=1).isoformat())
    to_date_str = request.GET.get('to_date', today.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = today.replace(day=1)
        to_date = today
    
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Generate date range
    date_range = []
    current_date = from_date
    holidays = Holiday.objects.filter(date__range=[from_date, to_date])
    holiday_dates = {h.date for h in holidays}
    
    while current_date <= to_date:
        is_holiday = current_date in holiday_dates or current_date.weekday() == 6
        date_range.append({
            'date': current_date,
            'is_holiday': is_holiday
        })
        current_date += timedelta(days=1)
    
    # Get attendance data
    attendance_records = Attendance.objects.filter(
        date__range=[from_date, to_date],
        user__in=employees
    ).select_related('user')
    
    attendance_dict = {}
    for record in attendance_records:
        if record.user.employee_id not in attendance_dict:
            attendance_dict[record.user.employee_id] = {}
        
        status_code = 'P' if record.status == 'present' else 'A' if record.status == 'absent' else 'H' if record.status == 'half_day' else 'NM'
        if record.check_in_time and record.check_in_time > time(9, 30) and record.status in ['present', 'half_day']:
            status_code += '*'  # Late indicator
        
        attendance_dict[record.user.employee_id][record.date] = status_code
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="detailed_attendance_{from_date}_{to_date}.csv"'
        
        writer = csv.writer(response)
        
        # Header
        header = ['Employee ID', 'DCCB', 'Designation']
        for date_info in date_range:
            date_str = date_info['date'].strftime('%d-%b')
            if date_info['is_holiday']:
                date_str += ' (HOL)'
            header.append(date_str)
        writer.writerow(header)
        
        # Data rows
        for employee in employees:
            row = [employee.employee_id, employee.dccb or '', employee.designation]
            for date_info in date_range:
                if date_info['is_holiday']:
                    row.append('HOL')
                else:
                    row.append(attendance_dict.get(employee.employee_id, {}).get(date_info['date'], 'NM'))
            writer.writerow(row)
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)

@login_required
@admin_required
def export_employees(request):
    """Export employee list"""
    format_type = request.GET.get('format', 'csv')
    
    # Apply same filters as employee list
    employees = CustomUser.objects.filter(role='field_officer').select_related()
    
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    dccb_filter = request.GET.get('dccb', '')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    designation_filter = request.GET.get('designation', '')
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employees_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Header with metadata
        writer.writerow([f'Employee Master List - Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([f'Total Records: {employees.count()}'])
        writer.writerow([])  # Empty row
        
        # Column headers
        writer.writerow([
            'Employee ID', 'Full Name', 'Designation', 'Contact Number', 
            'DCCB', 'Reporting Manager', 'Registration Date', 'Status'
        ])
        
        # Data rows
        for emp in employees:
            writer.writerow([
                emp.employee_id,
                f'{emp.first_name} {emp.last_name}',
                emp.designation,
                emp.contact_number,
                emp.dccb or '',
                emp.reporting_manager or '',
                emp.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'Active' if emp.is_active else 'Inactive'
            ])
        
        return response
    
@login_required
@admin_required
def employee_detail(request, employee_id):
    """Employee detail view for editing"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    context = {
        'employee': employee,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'dccb_choices': CustomUser.DCCB_CHOICES,
    }
    
    return render(request, 'authe/employee_detail.html', context)

@login_required
@admin_required
@require_http_methods(["PATCH"])
def activate_employee(request, employee_id):
    """Activate employee account"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    if employee.is_active:
        return JsonResponse({'success': False, 'error': 'Employee already active'}, status=400)
    
    try:
        with transaction.atomic():
            # Store before data
            before_data = f"Status: {'Active' if employee.is_active else 'Inactive'}"
            
            # Activate employee
            employee.is_active = True
            employee.save()
            
            # Create audit log
            after_data = f"Status: {'Active' if employee.is_active else 'Inactive'}"
            create_audit_log(
                request.user,
                f'Employee Activated: {employee.employee_id}',
                request,
                f'Before: {before_data}, After: {after_data}'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Employee {employee.employee_id} has been activated'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def export_employees(request):
    """Export employee list"""
    format_type = request.GET.get('format', 'csv')
    
    employees = CustomUser.objects.filter(role='field_officer').select_related()
    
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    dccb_filter = request.GET.get('dccb', '')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    designation_filter = request.GET.get('designation', '')
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employees_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Full Name', 'Designation', 'Contact Number', 'DCCB', 'Reporting Manager', 'Registration Date', 'Status'])
        
        for emp in employees:
            writer.writerow([
                emp.employee_id,
                f'{emp.first_name} {emp.last_name}',
                emp.designation,
                emp.contact_number,
                emp.dccb or '',
                emp.reporting_manager or '',
                emp.date_joined.strftime('%Y-%m-%d'),
                'Active' if emp.is_active else 'Inactive'
            ])
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)

@login_required
@admin_required
def export_attendance_daily(request):
    """Export daily attendance data in multiple formats"""
    format_type = request.GET.get('format', 'csv')
    
    from datetime import datetime, timedelta
    from .models import Holiday
    
    today = timezone.localdate()
    from_date_str = request.GET.get('from_date', (today - timedelta(days=today.weekday())).isoformat())
    to_date_str = request.GET.get('to_date', today.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = today - timedelta(days=today.weekday())
        to_date = today
    
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    date_range = []
    current_date = from_date
    holidays = Holiday.objects.filter(date__range=[from_date, to_date])
    holiday_dates = {h.date for h in holidays}
    
    while current_date <= to_date:
        is_holiday = current_date in holiday_dates or current_date.weekday() == 6
        date_range.append({'date': current_date, 'is_holiday': is_holiday})
        current_date += timedelta(days=1)
    
    attendance_records = Attendance.objects.filter(date__range=[from_date, to_date], user__in=employees).select_related('user')
    
    attendance_dict = {}
    for record in attendance_records:
        if record.user.employee_id not in attendance_dict:
            attendance_dict[record.user.employee_id] = {}
        
        status_code = 'P' if record.status == 'present' else 'A' if record.status == 'absent' else 'H' if record.status == 'half_day' else 'NM'
        if record.check_in_time and record.check_in_time > time(9, 30) and record.status in ['present', 'half_day']:
            status_code += '*'
        
        attendance_dict[record.user.employee_id][record.date] = status_code
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="daily_attendance_{from_date}_{to_date}.csv"'
        
        writer = csv.writer(response)
        header = ['Employee ID', 'DCCB', 'Designation']
        for date_info in date_range:
            header.append(date_info['date'].strftime('%d-%b'))
        writer.writerow(header)
        
        for employee in employees:
            row = [employee.employee_id, employee.dccb or '', employee.designation]
            for date_info in date_range:
                if date_info['is_holiday']:
                    row.append('HOL')
                else:
                    row.append(attendance_dict.get(employee.employee_id, {}).get(date_info['date'], 'NM'))
            writer.writerow(row)
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)
@login_required
@admin_required
@require_http_methods(["POST"])
def update_attendance_status(request):
    """Admin-only function to update attendance status"""
    try:
        data = json.loads(request.body)
        attendance_id = data.get('attendance_id')
        new_status = data.get('status')
        admin_remarks = data.get('remarks', '')
        
        if new_status not in ['present', 'absent', 'half_day']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Get attendance record
        attendance = get_object_or_404(Attendance, id=attendance_id)
        
        # Store before data for audit
        before_data = f"Status: {attendance.status}, Time: {attendance.check_in_time}"
        
        # Update attendance
        old_status = attendance.status
        attendance.status = new_status
        
        # If changing to absent, clear check-in time
        if new_status == 'absent':
            attendance.check_in_time = None
        # If changing from absent to present/half_day, set current time if no time exists
        elif old_status == 'absent' and new_status in ['present', 'half_day'] and not attendance.check_in_time:
            attendance.check_in_time = timezone.localtime().time()
        
        attendance.remarks = admin_remarks
        attendance.save()
        
        # Create audit log
        after_data = f"Status: {attendance.status}, Time: {attendance.check_in_time}"
        create_audit_log(
            request.user,
            f'Attendance Status Updated by Admin: {attendance.user.employee_id}',
            request,
            f'Before: {before_data}, After: {after_data}, Remarks: {admin_remarks}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance status updated to {new_status}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@admin_required
def employee_attendance_history(request, employee_id):
    """View individual employee attendance history"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    # Get date range (default: current month)
    today = timezone.localdate()
    from_date_str = request.GET.get('from_date', today.replace(day=1).isoformat())
    to_date_str = request.GET.get('to_date', today.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = today.replace(day=1)
        to_date = today
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        user=employee,
        date__range=[from_date, to_date]
    ).order_by('-date')
    
    # Get leave records for the period
    leave_records = LeaveRequest.objects.filter(
        user=employee,
        start_date__lte=to_date,
        end_date__gte=from_date,
        status='approved'
    )
    
    # Calculate statistics
    total_days = (to_date - from_date).days + 1
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    half_day_count = attendance_records.filter(status='half_day').count()
    late_count = attendance_records.filter(status__in=['present', 'half_day'], check_in_time__gt=time(10, 0)).count()
    
    # Pagination
    paginator = Paginator(attendance_records, 31)  # One month per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employee': employee,
        'page_obj': page_obj,
        'leave_records': leave_records,
        'from_date': from_date,
        'to_date': to_date,
        'stats': {
            'total_days': total_days,
            'present': present_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'late': late_count,
            'attendance_percentage': round((present_count + half_day_count * 0.5) / total_days * 100, 1) if total_days > 0 else 0
        }
    }
    
    return render(request, 'authe/admin_employee_attendance_history.html', context)