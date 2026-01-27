from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date, time
from .models import CustomUser, Attendance, LeaveRequest, AuditLog, TravelRequest
from .views import create_audit_log
import json
import csv
from io import StringIO
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

def check_pending_travel_requests(user, attendance_date):
    """Check if user has pending travel requests for the given date"""
    return TravelRequest.objects.filter(
        user=user,
        from_date__lte=attendance_date,
        to_date__gte=attendance_date,
        status='pending'
    ).exists()

def get_responsible_associate(user_dccb):
    """Get the Associate responsible for a given DCCB"""
    associates = CustomUser.objects.filter(
        designation='Associate',
        is_active=True
    )
    
    for assoc in associates:
        if assoc.multiple_dccb and user_dccb in assoc.multiple_dccb:
            return assoc
    return None

def admin_required(view_func):
    """Decorator to ensure only admin users can access admin views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Access denied. Please login.')
            return redirect('login')
        if request.user.role_level < 10:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('field_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
    """Decorator to ensure only admin users can access admin views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Access denied. Please login.')
            return redirect('login')
        if request.user.role_level < 10:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('field_dashboard')
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
    
    # Attendance KPIs for today - include DC confirmed records
    attendance_kpis = Attendance.objects.filter(date=today).aggregate(
        present=Count(Case(When(status='present', then=1), output_field=IntegerField())),
        absent=Count(Case(When(Q(status='absent') | Q(is_confirmed_by_dc=True, status='auto_not_marked'), then=1), output_field=IntegerField())),
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
    
    # Approval Status KPIs
    # DC Confirmation pending count
    dc_pending = Attendance.objects.filter(
        date__lte=today,
        is_confirmed_by_dc=False,
        status__in=['present', 'absent', 'half_day']
    ).count()
    
    # Admin Approval pending count (DC confirmed but not admin approved)
    admin_pending = Attendance.objects.filter(
        date__lte=today,
        is_confirmed_by_dc=True,
        is_approved_by_admin=False
    ).count()
    
    # Travel Approval pending count
    travel_pending = TravelRequest.objects.filter(status='pending').count()
    
    approval_status = {
        'dc_pending': dc_pending,
        'admin_pending': admin_pending,
        'travel_pending': travel_pending
    }
    
    # Pending leave requests
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'designation_counts': designation_counts,
        'dccb_counts': dccb_counts,
        'attendance_kpis': attendance_kpis,
        'approval_status': approval_status,
        'pending_leaves': pending_leaves,
        'today': today,
    }
    
    # Debug print to verify approval_status data
    print(f"DEBUG: approval_status = {approval_status}")
    
    return render(request, 'authe/admin_dashboard.html', context)

@login_required
@admin_required
def employee_list(request):
    """Comprehensive employee list view with filters and actions"""
    # Apply filters
    search = request.GET.get('search', '')
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    
    # Base query
    employees = CustomUser.objects.filter(role='field_officer').select_related()
    
    # Apply search filter
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Apply DCCB filter
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    # Apply designation filter
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Apply status filter
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    # Order by employee_id
    employees = employees.order_by('employee_id')
    
    # Pagination
    paginator = Paginator(employees, 25)  # 25 employees per page
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
        'total_employees': employees.count(),
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
    """Daily attendance matrix view with dynamic filters and search"""
    from datetime import datetime, timedelta
    from calendar import monthrange
    
    # Get date range and search parameters
    today = timezone.localdate()
    
    # Handle dynamic date range selection
    date_range_filter = request.GET.get('date_range', 'this_month')
    search = request.GET.get('search', '')
    
    # Calculate dates based on date range selection
    if date_range_filter == 'today':
        from_date = to_date = today
    elif date_range_filter == 'yesterday':
        from_date = to_date = today - timedelta(days=1)
    elif date_range_filter == 'this_week':
        from_date = today - timedelta(days=today.weekday())
        to_date = today
    elif date_range_filter == 'last_week':
        last_week_end = today - timedelta(days=today.weekday() + 1)
        from_date = last_week_end - timedelta(days=6)
        to_date = last_week_end
    elif date_range_filter == 'this_month':
        from_date = today.replace(day=1)
        # Get last day of current month
        _, last_day = monthrange(today.year, today.month)
        to_date = today.replace(day=last_day)
    elif date_range_filter == 'last_month':
        # Get first day of last month
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        from_date = first_day_last_month
        # Get last day of last month
        _, last_day = monthrange(first_day_last_month.year, first_day_last_month.month)
        to_date = first_day_last_month.replace(day=last_day)
    elif date_range_filter == 'last_7_days':
        from_date = today - timedelta(days=7)
        to_date = today
    elif date_range_filter == 'last_30_days':
        from_date = today - timedelta(days=30)
        to_date = today
    elif date_range_filter == 'custom':
        # Use provided dates or default to current month
        from_date_str = request.GET.get('from_date', today.replace(day=1).isoformat())
        to_date_str = request.GET.get('to_date')
        
        # If no to_date provided, calculate full month
        if not to_date_str:
            try:
                temp_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                _, last_day = monthrange(temp_date.year, temp_date.month)
                to_date_str = temp_date.replace(day=last_day).isoformat()
            except ValueError:
                _, last_day = monthrange(today.year, today.month)
                to_date_str = today.replace(day=last_day).isoformat()
        
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            from_date = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            to_date = today.replace(day=last_day)
    else:
        # Default to current month (full month)
        from_date = today.replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        to_date = today.replace(day=last_day)
    
    # Apply filters
    dccb_filter = request.GET.get('dccb', '')
    
    # Get employees with search functionality
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    
    # Apply search filter
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(dccb__icontains=search)
        )
    
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    # Generate complete date range
    date_range = []
    current_date = from_date
    
    # Get holidays safely
    try:
        from .models import Holiday
        holidays = Holiday.objects.filter(date__range=[from_date, to_date])
        holiday_dates = {h.date: h for h in holidays}
    except (ImportError, AttributeError):
        # If Holiday model doesn't exist, continue without holidays
        holiday_dates = {}
    
    # Generate all dates in range (including full month)
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
        
        # Determine final status considering DC confirmation
        final_status = record.status
        if record.is_confirmed_by_dc and record.status == 'auto_not_marked':
            final_status = 'absent'  # DC confirmed NM records become Absent
        
        attendance_dict[record.user.employee_id][record.date] = {
            'status': final_status,
            'is_late': is_late,
            'check_in_time': record.check_in_time,
            'is_dc_confirmed': record.is_confirmed_by_dc,
            'is_admin_approved': record.is_approved_by_admin,
            'is_leave_day': getattr(record, 'is_leave_day', False)
        }
    
    # Prepare final data structure
    attendance_data = []
    for employee in employees:
        employee_attendance = []
        
        for date_info in date_range:
            date_obj = date_info['date']
            attendance = attendance_dict.get(employee.employee_id, {}).get(date_obj, {})
            
            # Check if this employee has DC confirmed attendance for dates not in records
            status = attendance.get('status', 'not_marked')
            
            # If no attendance record exists, check if DC has confirmed this employee's attendance
            if status == 'not_marked':
                # Check if there's a DC confirmed record that would make this absent
                dc_confirmed_record = Attendance.objects.filter(
                    user=employee,
                    date=date_obj,
                    is_confirmed_by_dc=True
                ).first()
                
                if dc_confirmed_record:
                    status = 'absent'  # DC confirmed NM becomes Absent
            
            employee_attendance.append({
                'date': date_obj,
                'status': status,
                'is_late': attendance.get('is_late', False),
                'is_sunday': date_info['is_sunday'],
                'is_holiday': date_info['is_holiday'],
                'is_dc_confirmed': attendance.get('is_dc_confirmed', False),
                'is_admin_approved': attendance.get('is_admin_approved', False),
                'is_leave_day': attendance.get('is_leave_day', False)
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
        'search': search,
        'date_range_filter': date_range_filter,
        'dccb_filter': dccb_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'current_month': from_date.strftime('%B %Y'),
        'total_days': len(date_range),
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
    """Approve or reject leave request with automatic attendance marking"""
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
            
            # If leave is approved, create attendance records for leave dates
            if action == 'approve':
                from datetime import timedelta
                current_date = leave_request.start_date
                
                while current_date <= leave_request.end_date:
                    # Create or update attendance record for each leave date
                    attendance, created = Attendance.objects.get_or_create(
                        user=leave_request.user,
                        date=current_date,
                        defaults={
                            'status': 'absent',
                            'remarks': f'On approved leave: {leave_request.leave_type}',
                            'is_leave_day': True
                        }
                    )
                    
                    # If attendance already exists, update it to absent
                    if not created:
                        attendance.status = 'absent'
                        attendance.remarks = f'On approved leave: {leave_request.leave_type}'
                        attendance.is_leave_day = True
                        attendance.save()
                    
                    current_date += timedelta(days=1)
            
            # Create audit log
            after_data = f"Status: {leave_request.status}"
            create_audit_log(
                request.user,
                f'Leave Request {action.title()}d: {leave_request.id}',
                request,
                f'Before: {before_data}, After: {after_data}'
            )
            
            # Send notification to user
            from .notification_service import notify_leave_approval
            notify_leave_approval(leave_request, action == 'approve')
        
        return JsonResponse({
            'success': True,
            'message': f'Leave request {action}d successfully. Attendance automatically marked for leave dates.'
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
    
    # 1. Attendance Status Distribution - include DC confirmed
    status_counts = attendance_today.aggregate(
        present=Count(Case(When(status='present', then=1), output_field=IntegerField())),
        absent=Count(Case(When(Q(status='absent') | Q(is_confirmed_by_dc=True, status='auto_not_marked'), then=1), output_field=IntegerField())),
        half_day=Count(Case(When(status='half_day', then=1), output_field=IntegerField()))
    )
    not_marked = total_employees - sum(status_counts.values())
    attendance_percentage = round((status_counts['present'] + status_counts['half_day'] * 0.5) / total_employees * 100, 1) if total_employees > 0 else 0
    
    # 2. Late Arrival Distribution
    late_cutoff = time(9, 30)
    on_time = attendance_today.filter(status__in=['present', 'half_day'], check_in_time__lte=late_cutoff).count()
    late = attendance_today.filter(status__in=['present', 'half_day'], check_in_time__gt=late_cutoff).count()
    
    # 3. DCCB Attendance Comparison (top 6 DCCBs) - include DC confirmed
    dccb_stats = []
    dccb_attendance = CustomUser.objects.filter(role='field_officer', is_active=True, dccb__isnull=False).values('dccb').annotate(
        total=Count('id'),
        present_today=Count(Case(When(Q(attendance__date=today, attendance__status__in=['present', 'half_day']) | Q(attendance__date=today, attendance__is_confirmed_by_dc=True, attendance__status='absent'), then=1), output_field=IntegerField()))
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
    """API endpoint for map loading - simplified version"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    status_filter = request.GET.get('status', '')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    try:
        # Get all attendance records with GPS data
        attendance_query = Attendance.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user')
        
        # Apply date filter
        if date_str:
            attendance_query = attendance_query.filter(date=selected_date)
        
        # Apply status filter
        if status_filter:
            attendance_query = attendance_query.filter(status=status_filter)
        
        # If no records for selected date, show recent GPS data
        if not attendance_query.exists():
            attendance_query = Attendance.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).select_related('user').order_by('-date')[:20]
        
        # Build response data
        geo_data = []
        for record in attendance_query:
            try:
                lat = float(record.latitude)
                lng = float(record.longitude)
                
                # Calculate timing status
                timing_status = 'Not Marked'
                if record.check_in_time:
                    if record.check_in_time <= time(9, 30):
                        timing_status = 'On Time'
                    else:
                        timing_status = 'Late Arrival'
                
                geo_data.append({
                    'employee_id': record.user.employee_id,
                    'name': f"{record.user.first_name} {record.user.last_name}",
                    'designation': record.user.designation,
                    'dccb': record.user.dccb or 'Not Assigned',
                    'status': record.status,
                    'date': record.date.isoformat(),
                    'lat': lat,
                    'lng': lng,
                    'timing_status': timing_status,
                    'check_in_time': record.check_in_time.strftime('%H:%M') if record.check_in_time else 'Not Marked',
                    'location_address': record.location_address or f'GPS: {lat:.6f}, {lng:.6f}',
                    'location_accuracy': int(record.location_accuracy) if record.location_accuracy else 0
                })
            except (ValueError, TypeError) as e:
                continue
        
        return JsonResponse({
            'success': True,
            'count': len(geo_data),
            'selected_date': selected_date.isoformat(),
            'message': f'Found {len(geo_data)} GPS attendance records',
            'data': geo_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'selected_date': selected_date.isoformat(),
            'data': []
        })

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
    """Export daily attendance data with MIS report support"""
    try:
        format_type = request.GET.get('format', 'csv')
        report_type = request.GET.get('report_type', 'daily_attendance')
        date_str = request.GET.get('date', timezone.localdate().isoformat())
        
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.localdate()
        
        if report_type == 'dccb_summary':
            return export_dccb_daily_summary(selected_date)
        else:
            return export_daily_attendance_report(selected_date)
            
    except Exception as e:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', str(e)])
        return response

def export_dccb_daily_summary(selected_date):
    """Export DCCB-wise daily attendance summary"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dccb_summary_{selected_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['DCCB', 'Date', 'Check In Time', 'Present', 'Absent', 'Half Day', 'Not Marked', 'Late (Y/N)'])
    
    # Get all DCCBs
    dccbs = CustomUser.objects.filter(role='field_officer', is_active=True, dccb__isnull=False).values_list('dccb', flat=True).distinct()
    
    total_present = total_absent = total_half_day = total_not_marked = total_late = 0
    
    for dccb in dccbs:
        employees = CustomUser.objects.filter(role='field_officer', is_active=True, dccb=dccb)
        attendance_records = Attendance.objects.filter(user__in=employees, date=selected_date)
        
        present = attendance_records.filter(status='present').count()
        absent = attendance_records.filter(status='absent').count()
        half_day = attendance_records.filter(status='half_day').count()
        not_marked = employees.count() - attendance_records.count()
        late = attendance_records.filter(check_in_time__gt=time(9, 30)).count()
        
        # Get earliest check-in time for this DCCB
        earliest_checkin = attendance_records.filter(check_in_time__isnull=False).order_by('check_in_time').first()
        checkin_time = earliest_checkin.check_in_time.strftime('%H:%M') if earliest_checkin else 'N/A'
        
        writer.writerow([
            dccb,
            selected_date.strftime('%Y-%m-%d'),
            checkin_time,
            present,
            absent,
            half_day,
            not_marked,
            'Y' if late > 0 else 'N'
        ])
        
        total_present += present
        total_absent += absent
        total_half_day += half_day
        total_not_marked += not_marked
        total_late += late
    
    # Grand Total row
    writer.writerow([
        'GRAND TOTAL',
        selected_date.strftime('%Y-%m-%d'),
        'N/A',
        total_present,
        total_absent,
        total_half_day,
        total_not_marked,
        'Y' if total_late > 0 else 'N'
    ])
    
    return response

def export_daily_attendance_report(selected_date):
    """Export daily attendance report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="daily_attendance_{selected_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'Name', 'DCCB', 'Designation', 'Status', 'Check In Time', 'Late (Y/N)'])
    
    employees = CustomUser.objects.filter(role='field_officer', is_active=True).order_by('dccb', 'employee_id')
    
    for employee in employees:
        attendance = Attendance.objects.filter(user=employee, date=selected_date).first()
        
        if attendance:
            status = attendance.get_status_display()
            checkin_time = attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else 'N/A'
            is_late = 'Y' if attendance.check_in_time and attendance.check_in_time > time(9, 30) else 'N'
        else:
            status = 'Not Marked'
            checkin_time = 'N/A'
            is_late = 'N'
        
        writer.writerow([
            employee.employee_id,
            f'{employee.first_name} {employee.last_name}',
            employee.dccb or 'Not Assigned',
            employee.designation,
            status,
            checkin_time,
            is_late
        ])
    
    return response

def export_dccb_summary(request, format_type, from_date, to_date, dccb_filter):
    """Export DCCB-wise attendance summary"""
    from django.db.models import Count, Q
    
    # Get DCCB-wise summary
    dccb_query = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        dccb_query = dccb_query.filter(dccb=dccb_filter)
    
    dccb_summary = []
    total_present = total_absent = total_half_day = total_not_marked = total_employees = 0
    
    for dccb_choice in CustomUser.DCCB_CHOICES:
        dccb_code = dccb_choice[0]
        dccb_name = dccb_choice[1]
        
        if dccb_filter and dccb_filter != dccb_code:
            continue
            
        employees = dccb_query.filter(dccb=dccb_code)
        emp_count = employees.count()
        
        if emp_count == 0:
            continue
            
        # Calculate attendance stats for date range
        present = Attendance.objects.filter(
            user__in=employees, date__range=[from_date, to_date], status='present'
        ).count()
        
        absent = Attendance.objects.filter(
            user__in=employees, date__range=[from_date, to_date], status='absent'
        ).count()
        
        half_day = Attendance.objects.filter(
            user__in=employees, date__range=[from_date, to_date], status='half_day'
        ).count()
        
        # Calculate not marked (total possible days - marked days)
        days_in_range = (to_date - from_date).days + 1
        total_possible = emp_count * days_in_range
        marked = present + absent + half_day
        not_marked = total_possible - marked
        
        dccb_summary.append({
            'dccb': dccb_name,
            'present': present,
            'absent': absent,
            'half_day': half_day,
            'not_marked': not_marked,
            'total': emp_count
        })
        
        # Add to totals
        total_present += present
        total_absent += absent
        total_half_day += half_day
        total_not_marked += not_marked
        total_employees += emp_count
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="dccb_summary_{from_date}_{to_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['DCCB', 'Present', 'Absent', 'Half Day', 'Not Marked', 'Total Employees'])
        
        for summary in dccb_summary:
            writer.writerow([
                summary['dccb'], summary['present'], summary['absent'],
                summary['half_day'], summary['not_marked'], summary['total']
            ])
        
        # Add total row
        writer.writerow([
            'GRAND TOTAL', total_present, total_absent,
            total_half_day, total_not_marked, total_employees
        ])
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)

def export_employee_list(request, format_type, from_date, to_date):
    """Export employee-level attendance list"""
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    attendance_records = Attendance.objects.filter(
        date__range=[from_date, to_date], user__in=employees
    ).select_related('user').order_by('date', 'user__employee_id')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employee_attendance_{from_date}_{to_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'DCCB', 'Date', 'Marked Attendance (P/A/H)',
            'Not Marked (Yes/No)', 'Time Status (On Time/Late)'
        ])
        
        for record in attendance_records:
            # Determine status
            if record.status == 'present':
                marked_status = 'P'
            elif record.status == 'absent':
                marked_status = 'A'
            elif record.status == 'half_day':
                marked_status = 'H'
            else:
                marked_status = 'NM'
            
            not_marked = 'Yes' if marked_status == 'NM' else 'No'
            
            # Determine time status
            time_status = 'Not Marked'
            if record.check_in_time:
                time_status = 'On Time' if record.check_in_time <= time(9, 30) else 'Late'
            
            writer.writerow([
                record.user.employee_id,
                record.user.dccb or 'Not Assigned',
                record.date.strftime('%Y-%m-%d'),
                marked_status,
                not_marked,
                time_status
            ])
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)

def export_standard_attendance(request, format_type, from_date, to_date, dccb_filter):
    """Standard attendance export (existing functionality)"""
    try:
        employees = CustomUser.objects.filter(role='field_officer', is_active=True)
        if dccb_filter:
            employees = employees.filter(dccb=dccb_filter)
        
        date_range = []
        current_date = from_date
        
        # Get holidays safely
        try:
            from .models import Holiday
            holidays = Holiday.objects.filter(date__range=[from_date, to_date])
            holiday_dates = {h.date for h in holidays}
        except:
            holiday_dates = set()
        
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
                status_code += '*'  # Late indicator
            
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
        
    except Exception as e:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_standard_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Details'])
        writer.writerow(['Standard Export Error', str(e)])
        return response
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
        
        # Notify user if MT or Support
        if attendance.user.designation in ['MT', 'Support']:
            from .notification_service import create_notification
            create_notification(
                recipient=attendance.user,
                notification_type='system_alert',
                title='Attendance Updated by Admin',
                message=f'Your attendance status has been updated to {new_status} by Admin {request.user.employee_id}',
                priority='medium'
            )
        
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
def approval_status(request):
    """Main approval status dashboard"""
    today = timezone.localdate()
    
    # Calculate approval status counts
    dc_pending = Attendance.objects.filter(
        date__lte=today,
        is_confirmed_by_dc=False,
        status__in=['present', 'absent', 'half_day']
    ).count()
    
    admin_pending = Attendance.objects.filter(
        date__lte=today,
        is_confirmed_by_dc=True,
        is_approved_by_admin=False
    ).count()
    
    from .models import TravelRequest
    travel_pending = TravelRequest.objects.filter(status='pending').count()
    
    context = {
        'dc_pending': dc_pending,
        'admin_pending': admin_pending,
        'travel_pending': travel_pending,
        'today': today
    }
    
    return render(request, 'authe/admin_approval_status.html', context)

@login_required
@admin_required
def dc_confirmation(request):
    """DC confirmation screen with travel request validation"""
    from datetime import datetime, timedelta
    
    # Get date range (default: last 7 days)
    today = timezone.localdate()
    default_from = today - timedelta(days=7)
    
    from_date_str = request.GET.get('from_date', default_from.isoformat())
    to_date_str = request.GET.get('to_date', today.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = default_from
        to_date = today
    
    # Apply filters
    dccb_filter = request.GET.get('dccb', '')
    employee_id_filter = request.GET.get('employee_id', '')
    
    # Get pending DC confirmations only (exclude DC users)
    attendance_query = Attendance.objects.filter(
        date__range=[from_date, to_date],
        is_confirmed_by_dc=False,
        status__in=['present', 'absent', 'half_day']
    ).exclude(user__designation='DC').select_related('user')
    
    if dccb_filter:
        attendance_query = attendance_query.filter(user__dccb=dccb_filter)
    if employee_id_filter:
        attendance_query = attendance_query.filter(user__employee_id__icontains=employee_id_filter)
    
    # Check for travel request restrictions
    blocked_records = []
    for attendance in attendance_query:
        if check_pending_travel_requests(attendance.user, attendance.date):
            blocked_records.append({
                'attendance': attendance,
                'reason': 'Pending travel request approval required'
            })
    
    # Pagination
    paginator = Paginator(attendance_query, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'dccb_filter': dccb_filter,
        'employee_id_filter': employee_id_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'blocked_records': blocked_records,
    }
    
    return render(request, 'authe/admin_dc_confirmation.html', context)

@login_required
@admin_required
def admin_approval(request):
    """Admin approval screen with travel request validation"""
    from datetime import datetime, timedelta
    
    # Handle CSV export
    if request.GET.get('format') == 'csv':
        return export_admin_approval_records(request)
    
    # Get payroll cycle dates (25th to 25th)
    today = timezone.localdate()
    if today.day >= 25:
        cycle_start = today.replace(day=25)
        next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        cycle_end = next_month.replace(day=25)
    else:
        cycle_end = today.replace(day=25)
        prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=25)
        cycle_start = prev_month
    
    from_date_str = request.GET.get('from_date', cycle_start.isoformat())
    to_date_str = request.GET.get('to_date', cycle_end.isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = cycle_start
        to_date = cycle_end
    
    # Apply filters
    employee_id_filter = request.GET.get('employee_id', '')
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    approval_status_filter = request.GET.get('approval_status', '')
    
    # Get attendance records for admin approval
    # Associates: Direct admin approval (no DC confirmation needed)
    # DC: Direct admin approval (no DC confirmation needed) - BUT check travel requests
    # MT/DC/Support: Require DC confirmation first
    base_query = Attendance.objects.filter(
        date__range=[from_date, to_date]
    ).filter(
        Q(user__designation__in=['Associate', 'DC']) |  # Associates and DCs can be approved directly
        Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)  # MT/Support need DC confirmation first
    ).select_related('user')
    
    # Apply approval status filter
    if approval_status_filter == 'pending':
        attendance_records = base_query.filter(is_approved_by_admin=False)
    elif approval_status_filter == 'approved':
        attendance_records = base_query.filter(is_approved_by_admin=True)
    else:
        attendance_records = base_query  # Show all (both pending and approved)
    
    attendance_records = attendance_records.order_by('-date', 'user__employee_id')
    
    if employee_id_filter:
        attendance_records = attendance_records.filter(user__employee_id__icontains=employee_id_filter)
    if dccb_filter:
        attendance_records = attendance_records.filter(user__dccb=dccb_filter)
    if designation_filter:
        attendance_records = attendance_records.filter(user__designation=designation_filter)
    
    # Check for travel request restrictions for DC users
    blocked_records = []
    for attendance in attendance_records:
        if attendance.user.designation == 'DC' and check_pending_travel_requests(attendance.user, attendance.date):
            blocked_records.append({
                'attendance': attendance,
                'reason': 'Pending travel request approval required'
            })
    
    # Pagination
    paginator = Paginator(attendance_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id_filter': employee_id_filter,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'approval_status_filter': approval_status_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'cycle_start': cycle_start,
        'cycle_end': cycle_end,
        'blocked_records': blocked_records,
    }
    
    return render(request, 'authe/admin_approval.html', context)

@login_required
@admin_required
def todays_attendance_details(request):
    """Today's Attendance Details screen with simplified filtering"""
    # Handle CSV export
    if request.GET.get('format') == 'csv':
        return export_todays_attendance(request)
    
    # Get selected date (default to today)
    selected_date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    # Get search parameter
    search = request.GET.get('search', '')
    
    # Get attendance records for the selected date
    attendance_query = Attendance.objects.filter(date=selected_date).select_related('user')
    
    # Apply universal search filter
    if search:
        attendance_query = attendance_query.filter(
            Q(user__employee_id__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__dccb__icontains=search) |
            Q(user__designation__icontains=search) |
            Q(status__icontains=search) |
            Q(task__icontains=search) |
            Q(workplace__icontains=search)
        )
    
    # Order by check-in time (nulls last)
    attendance_query = attendance_query.order_by('check_in_time', 'user__employee_id')
    
    # Pagination
    paginator = Paginator(attendance_query, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary stats
    total_records = attendance_query.count()
    present_count = attendance_query.filter(status='present').count()
    absent_count = attendance_query.filter(status='absent').count()
    half_day_count = attendance_query.filter(status='half_day').count()
    late_count = attendance_query.filter(check_in_time__gt=time(9, 30)).count()
    
    context = {
        'page_obj': page_obj,
        'selected_date': selected_date,
        'search': search,
        'summary': {
            'total': total_records,
            'present': present_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'late': late_count
        }
    }
    
    return render(request, 'authe/todays_attendance_details.html', context)

@login_required
@admin_required
def export_todays_attendance(request):
    """Export today's attendance records to CSV"""
    today = timezone.localdate()
    
    try:
        # Get all today's attendance records
        attendance_records = Attendance.objects.filter(date=today).select_related('user').order_by('check_in_time', 'user__employee_id')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="todays_attendance_{today.strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Employee ID', 'Employee Name', 'DCCB', 'Designation', 'Check-In Time', 
            'Check-Out Time', 'Attendance Status', 'Time Status', 'Travel Status', 
            'Travel Approved', 'Task', 'Work Place', 'Location', 'DC Confirmation', 
            'Approval Status', 'Remarks'
        ])
        
        # Write data rows
        for attendance in attendance_records:
            try:
                # Determine time status
                time_status = 'Not Marked'
                if attendance.check_in_time:
                    time_status = 'On Time' if attendance.check_in_time <= time(9, 30) else 'Late'
                
                # Location info
                location = ''
                if attendance.latitude and attendance.longitude:
                    location = f"{attendance.latitude:.6f}, {attendance.longitude:.6f}"
                
                writer.writerow([
                    attendance.user.employee_id,
                    f"{attendance.user.first_name} {attendance.user.last_name}",
                    attendance.user.dccb or 'Not Assigned',
                    attendance.user.designation,
                    attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else 'NM',
                    attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else 'NM',
                    attendance.get_status_display(),
                    time_status,
                    'Yes' if attendance.travel_required else 'No',
                    'Yes' if attendance.travel_approved else 'No',
                    attendance.task or 'NM',
                    attendance.workplace or 'NM',
                    location or 'NM',
                    'Done' if attendance.is_confirmed_by_dc else 'Pending',
                    'Approved' if attendance.is_approved_by_admin else 'Pending',
                    attendance.remarks or 'NM'
                ])
            except Exception as e:
                writer.writerow([f'Error processing record {attendance.id}: {str(e)}', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
        
        return response
        
    except Exception as e:
        # Return error as CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_todays_attendance_{today.strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Details'])
        writer.writerow(['Export Error', str(e)])
        return response

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
    
    # Calculate statistics
    total_days = (to_date - from_date).days + 1
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    half_day_count = attendance_records.filter(status='half_day').count()
    
    # Pagination
    paginator = Paginator(attendance_records, 31)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employee': employee,
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'stats': {
            'total_days': total_days,
            'present': present_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'attendance_percentage': round((present_count + half_day_count * 0.5) / total_days * 100, 1) if total_days > 0 else 0
        }
    }
    
    return render(request, 'authe/admin_employee_attendance_history.html', context)
    
    try:
        # Get all today's attendance records
        attendance_records = Attendance.objects.filter(date=today).select_related('user').order_by('check_in_time', 'user__employee_id')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="todays_attendance_{today.strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Employee ID', 'Employee Name', 'DCCB', 'Designation', 'Check-In Time', 
            'Check-Out Time', 'Attendance Status', 'Time Status', 'Travel Status', 
            'Travel Approved', 'Task', 'Work Place', 'Location', 'DC Confirmation', 
            'Approval Status', 'Remarks'
        ])
        
        # Write data rows
        for attendance in attendance_records:
            try:
                # Determine time status
                time_status = 'Not Marked'
                if attendance.check_in_time:
                    time_status = 'On Time' if attendance.check_in_time <= time(9, 30) else 'Late'
                
                # Location info
                location = ''
                if attendance.latitude and attendance.longitude:
                    location = f"{attendance.latitude:.6f}, {attendance.longitude:.6f}"
                
                writer.writerow([
                    attendance.user.employee_id,
                    f"{attendance.user.first_name} {attendance.user.last_name}",
                    attendance.user.dccb or 'Not Assigned',
                    attendance.user.designation,
                    attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else 'NM',
                    attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else 'NM',
                    attendance.get_status_display(),
                    time_status,
                    'Yes' if attendance.travel_required else 'No',
                    'Yes' if attendance.travel_approved else 'No',
                    attendance.task or 'NM',
                    attendance.workplace or 'NM',
                    location or 'NM',
                    'Done' if attendance.is_confirmed_by_dc else 'Pending',
                    'Approved' if attendance.is_approved_by_admin else 'Pending',
                    attendance.remarks or 'NM'
                ])
            except Exception as e:
                writer.writerow([f'Error processing record {attendance.id}: {str(e)}', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
        
        return response
        
    except Exception as e:
        # Return error as CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_todays_attendance_{today.strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Details'])
        writer.writerow(['Export Error', str(e)])
        return response
    """Export admin approval attendance records to CSV"""
    try:
        # Get all DC confirmed attendance records
        attendance_records = Attendance.objects.filter(
            is_confirmed_by_dc=True
        ).select_related('user', 'approved_by_admin').order_by('-date')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="admin_approval_records_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Employee ID', 'Employee Name', 'DCCB', 'Designation', 'Date', 
            'Status', 'Check In Time', 'DC Confirmed', 'Admin Approved', 
            'Approved By', 'Approved At', 'Remarks'
        ])
        
        # Write debug info
        writer.writerow([f'Total Records Found: {attendance_records.count()}', '', '', '', '', '', '', '', '', '', '', ''])
        
        # Write data rows
        for attendance in attendance_records:
            try:
                writer.writerow([
                    attendance.user.employee_id,
                    f"{attendance.user.first_name} {attendance.user.last_name}",
                    attendance.user.dccb or 'Not Assigned',
                    attendance.user.designation,
                    attendance.date.strftime('%Y-%m-%d'),
                    attendance.get_status_display(),
                    attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else '',
                    'Yes' if attendance.is_confirmed_by_dc else 'No',
                    'Yes' if attendance.is_approved_by_admin else 'No',
                    attendance.approved_by_admin.employee_id if attendance.approved_by_admin else '',
                    attendance.admin_approved_at.strftime('%Y-%m-%d %H:%M:%S') if attendance.admin_approved_at else '',
                    attendance.remarks or ''
                ])
            except Exception as e:
                writer.writerow([f'Error processing record {attendance.id}: {str(e)}', '', '', '', '', '', '', '', '', '', '', ''])
        
        return response
        
    except Exception as e:
        # Return error as CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_admin_approval_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Details'])
        writer.writerow(['Export Error', str(e)])
        return response

@login_required
@admin_required
def travel_approval(request):
    """Travel approval screen"""
    from datetime import datetime, timedelta
    
    # Get date range (default: last 90 days to capture more records)
    today = timezone.localdate()
    default_from = today - timedelta(days=90)
    
    from_date_str = request.GET.get('from_date', default_from.isoformat())
    to_date_str = request.GET.get('to_date', (today + timedelta(days=30)).isoformat())
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        from_date = default_from
        to_date = today + timedelta(days=30)
    
    # Apply filters
    employee_id_filter = request.GET.get('employee_id', '')
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Get travel requests - show all travel requests for admin monitoring
    travel_query = TravelRequest.objects.all().select_related('user', 'request_to').order_by('-created_at')
    
    # Apply filters
    if employee_id_filter:
        travel_query = travel_query.filter(user__employee_id__icontains=employee_id_filter)
    if dccb_filter:
        travel_query = travel_query.filter(user__dccb=dccb_filter)
    if designation_filter:
        travel_query = travel_query.filter(user__designation=designation_filter)
    
    # Apply date filter on created_at instead of travel dates for broader search
    travel_query = travel_query.filter(created_at__date__range=[from_date, to_date])
    
    # Debug: Print query count
    print(f"DEBUG: Total travel requests found: {travel_query.count()}")
    print(f"DEBUG: Date range: {from_date} to {to_date}")
    
    # Pagination
    paginator = Paginator(travel_query, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id_filter': employee_id_filter,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
    }
    
    return render(request, 'authe/admin_travel_approval.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def bulk_approve_attendance(request):
    """Bulk approve attendance records with travel request validation"""
    try:
        data = json.loads(request.body)
        attendance_ids = data.get('attendance_ids', [])
        
        if not attendance_ids:
            return JsonResponse({'success': False, 'error': 'No attendance records selected'}, status=400)
        
        with transaction.atomic():
            # Get attendance records - Associates don't need DC confirmation
            attendance_records = Attendance.objects.filter(
                id__in=attendance_ids,
                is_approved_by_admin=False
            ).filter(
                Q(user__designation='Associate') |  # Associates don't need DC confirmation
                Q(user__designation__in=['DC', 'MT', 'Support'], is_confirmed_by_dc=True)  # Others need DC confirmation
            ).select_related('user')
            
            blocked_records = []
            approved_records = []
            
            for attendance in attendance_records:
                # Check for pending travel requests for DC users
                if attendance.user.designation == 'DC' and check_pending_travel_requests(attendance.user, attendance.date):
                    # Find responsible Associate
                    responsible_associate = get_responsible_associate(attendance.user.dccb)
                    
                    blocked_records.append({
                        'employee_id': attendance.user.employee_id,
                        'date': attendance.date,
                        'reason': f'Pending travel request approval from Associate {responsible_associate.employee_id if responsible_associate else "(Not Found)"}'
                    })
                    
                    # Send notification to Admin about blocked approval
                    from .notification_service import NotificationService
                    NotificationService.create_notification(
                        recipient=request.user,
                        notification_type='system_alert',
                        title='Attendance Approval Blocked',
                        message=f'Cannot approve attendance for DC {attendance.user.employee_id} on {attendance.date} due to pending travel request approval.',
                        priority='high'
                    )
                    
                    # Send notification to Associate
                    if responsible_associate:
                        NotificationService.create_notification(
                            recipient=responsible_associate,
                            notification_type='travel_request',
                            title='Urgent: Travel Request Approval Required',
                            message=f'Admin cannot approve DC attendance for {attendance.user.employee_id} on {attendance.date}. Please review pending travel request.',
                            priority='urgent'
                        )
                    
                    continue
                
                approved_records.append(attendance)
            
            # Update only non-blocked attendance records
            if approved_records:
                approved_ids = [att.id for att in approved_records]
                updated_count = Attendance.objects.filter(id__in=approved_ids).update(
                    is_approved_by_admin=True,
                    approved_by_admin=request.user,
                    admin_approved_at=timezone.now()
                )
                
                # Notify users about admin approval
                from .notification_service import notify_admin_approval_to_user
                for attendance in approved_records:
                    notify_admin_approval_to_user(attendance.user, request.user)
                
                # Convert NM to Absent for approved records
                Attendance.objects.filter(
                    id__in=approved_ids,
                    status='auto_not_marked',
                    is_approved_by_admin=True
                ).update(status='absent')
            else:
                updated_count = 0
            
            # Create audit log
            create_audit_log(
                request.user,
                f'Bulk Attendance Approval: {updated_count} approved, {len(blocked_records)} blocked',
                request,
                f'Approved IDs: {[att.id for att in approved_records]}, Blocked: {len(blocked_records)} due to pending travel requests'
            )
        
        response_message = f'Successfully approved {updated_count} attendance records'
        if blocked_records:
            response_message += f'. {len(blocked_records)} records blocked due to pending travel requests.'
        
        return JsonResponse({
            'success': True,
            'message': response_message,
            'approved_count': updated_count,
            'blocked_records': blocked_records
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def export_travel_requests(request):
    """Export all travel requests to CSV with debug info"""
    try:
        # Get ALL travel requests
        travel_requests = TravelRequest.objects.all().select_related('user', 'request_to').order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="all_travel_requests_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Employee ID', 'Employee Name', 'DCCB', 'Designation', 'Travel Date', 
            'Duration', 'ER ID', 'Distance (KM)', 'Address', 'Contact Person', 
            'Purpose', 'Status', 'Approved By', 'Approved At', 'Remarks', 'Created At'
        ])
        
        # Write debug info as first row
        writer.writerow([f'Total Records Found: {travel_requests.count()}', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
        
        # Write data rows
        for travel in travel_requests:
            try:
                travel_date = travel.from_date.strftime('%d %b %Y')
                if travel.from_date != travel.to_date:
                    travel_date += f" - {travel.to_date.strftime('%d %b %Y')}"
                
                approved_by = ''
                if travel.request_to:
                    approved_by = f"{travel.request_to.first_name} {travel.request_to.last_name}"
                
                writer.writerow([
                    travel.user.employee_id,
                    f"{travel.user.first_name} {travel.user.last_name}",
                    travel.user.dccb or 'Not Assigned',
                    travel.user.designation,
                    travel_date,
                    travel.get_duration_display(),
                    travel.er_id,
                    travel.distance_km,
                    travel.address,
                    travel.contact_person,
                    travel.purpose,
                    travel.get_status_display(),
                    approved_by,
                    travel.approved_at.strftime('%Y-%m-%d %H:%M:%S') if travel.approved_at else '',
                    travel.remarks or '',
                    travel.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            except Exception as e:
                writer.writerow([f'Error processing record {travel.id}: {str(e)}', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
        
        return response
        
    except Exception as e:
        # Return error as CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="error_debug_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Details'])
        writer.writerow(['Export Error', str(e)])
        return response

@login_required
@admin_required
def admin_direct_approval(request):
    """Admin can directly approve DC attendance (bypassing DC confirmation step)"""
    selected_date = request.GET.get('date', timezone.localdate().isoformat())
    
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        date_obj = timezone.localdate()
    
    if request.method == 'POST':
        attendance_ids = request.POST.getlist('attendance_ids')
        action = request.POST.get('action')
        
        if action == 'approve_direct' and attendance_ids:
            updated_count = 0
            for att_id in attendance_ids:
                try:
                    attendance = Attendance.objects.get(id=att_id)
                    # Admin directly approves DC attendance, bypassing DC confirmation
                    attendance.is_confirmed_by_dc = True
                    attendance.confirmed_by_dc = request.user
                    attendance.dc_confirmed_at = timezone.now()
                    attendance.is_approved_by_admin = True
                    attendance.approved_by_admin = request.user
                    attendance.admin_approved_at = timezone.now()
                    attendance.confirmation_source = 'ADMIN'
                    attendance.save()
                    updated_count += 1
                    
                    # Create notification for the DC
                    from .notification_service import NotificationService
                    NotificationService.create_notification(
                        recipient=attendance.user,
                        notification_type='system_alert',
                        title='Attendance Directly Approved by Admin',
                        message=f'Your attendance for {attendance.date.strftime("%d %b %Y")} has been directly approved by Admin {request.user.employee_id}.',
                        priority='medium'
                    )
                    
                except Attendance.DoesNotExist:
                    continue
            
            messages.success(request, f'Successfully approved {updated_count} DC attendance records directly.')
            return redirect('admin_direct_approval')
    
    # Get DC users attendance records that need direct admin approval
    dc_attendance = Attendance.objects.filter(
        date=date_obj,
        user__designation='DC',
        user__role='field_officer',
        is_approved_by_admin=False  # Only show unapproved records
    ).select_related('user').order_by('user__employee_id')
    
    context = {
        'attendance_records': dc_attendance,
        'selected_date': date_obj,
        'today': timezone.localdate(),
    }
    
    return render(request, 'authe/admin_direct_approval.html', context)