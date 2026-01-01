from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date, time
from .models import CustomUser, Attendance, LeaveRequest, AuditLog, Holiday, Notification
import json
import csv
import re
from io import StringIO
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

def admin_required(view_func):
    """Decorator to ensure only admin users can access admin views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def create_audit_log(admin_user, action, details=None, request=None):
    """Create audit log entry for admin actions"""
    ip_address = None
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
    
    AuditLog.objects.create(
        user=admin_user,
        action=action,
        details=details,
        ip_address=ip_address
    )

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard with KPIs"""
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
def employee_detail(request, employee_id):
    """Employee profile detail view with edit functionality"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    if request.method == 'GET':
        # Get recent audit logs for this employee
        audit_logs = AuditLog.objects.filter(
            details__icontains=employee_id
        ).order_by('-timestamp')[:10]
        
        context = {
            'employee': employee,
            'audit_logs': audit_logs,
            'dccb_choices': CustomUser.DCCB_CHOICES,
            'status_choices': CustomUser.STATUS_CHOICES,
        }
        
        return render(request, 'authe/admin_employee_detail.html', context)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Store before data for audit
            before_data = {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'email': employee.email,
                'contact_number': employee.contact_number,
                'dccb': employee.dccb,
                'reporting_manager': employee.reporting_manager,
                'status': employee.status,
                'registration_at': employee.registration_at.isoformat() if employee.registration_at else None
            }
            
            # Validate and update fields
            if 'first_name' in data and data['first_name'].strip():
                employee.first_name = data['first_name'].strip().upper()
            
            if 'last_name' in data and data['last_name'].strip():
                employee.last_name = data['last_name'].strip().upper()
            
            if 'email' in data:
                email = data['email'].strip()
                if email:
                    # Check if email is already taken by another user
                    existing_user = CustomUser.objects.filter(email=email).exclude(id=employee.id).first()
                    if existing_user:
                        return JsonResponse({'success': False, 'error': 'Email already exists for another user'}, status=400)
                    employee.email = email
                else:
                    employee.email = ''
            
            if 'contact_number' in data and data['contact_number'].strip():
                contact = data['contact_number'].strip()
                if not re.match(r'^\d{10}$', contact):
                    return JsonResponse({'success': False, 'error': 'Contact number must be exactly 10 digits'}, status=400)
                
                # Check if contact is already taken by another user
                existing_user = CustomUser.objects.filter(contact_number=contact).exclude(id=employee.id).first()
                if existing_user:
                    return JsonResponse({'success': False, 'error': 'Contact number already exists for another user'}, status=400)
                
                employee.contact_number = contact
            
            if 'dccb' in data:
                employee.dccb = data['dccb'] if data['dccb'] else None
            
            if 'reporting_manager' in data:
                manager = data['reporting_manager'].strip()
                employee.reporting_manager = manager.upper() if manager else None
            
            if 'status' in data and data['status'] in ['active', 'inactive']:
                employee.status = data['status']
            
            if 'registration_at' in data and data['registration_at']:
                try:
                    employee.registration_at = datetime.strptime(data['registration_at'], '%Y-%m-%dT%H:%M')
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid registration date format'}, status=400)
            
            with transaction.atomic():
                employee.save()
                
                # Create audit log
                after_data = {
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'email': employee.email,
                    'contact_number': employee.contact_number,
                    'dccb': employee.dccb,
                    'reporting_manager': employee.reporting_manager,
                    'status': employee.status,
                    'registration_at': employee.registration_at.isoformat() if employee.registration_at else None
                }
                
                # Find what changed
                changes = []
                for key, new_value in after_data.items():
                    old_value = before_data.get(key)
                    if old_value != new_value:
                        changes.append(f"{key}: '{old_value}' → '{new_value}'")
                
                if changes:
                    create_audit_log(
                        request.user,
                        f'Employee Profile Updated: {employee.employee_id}',
                        f'Changes: {', '.join(changes)}',
                        request
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Employee profile updated successfully',
                'employee': {
                    'full_name': employee.full_name,
                    'email': employee.email,
                    'contact_number': employee.contact_number,
                    'dccb': employee.dccb,
                    'reporting_manager': employee.reporting_manager,
                    'status': employee.status
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
@admin_required
def employee_list(request):
    """Employee master list with filters and pagination"""
    # Start with all field officers
    employees = CustomUser.objects.filter(role='field_officer').order_by('-registration_at')
    
    # Apply search filter
    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(contact_number__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Apply DCCB filter
    dccb_filter = request.GET.get('dccb', '').strip()
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    
    # Apply designation filter
    designation_filter = request.GET.get('designation', '').strip()
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Apply status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    # Debug: Print filter values and count
    print(f"Search: '{search}', DCCB: '{dccb_filter}', Designation: '{designation_filter}', Status: '{status_filter}'")
    print(f"Total employees after filters: {employees.count()}")
    
    # Pagination
    paginator = Paginator(employees, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'status_choices': CustomUser.STATUS_CHOICES,
        'total_count': employees.count(),
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
        before_data = f"Name: {employee.first_name} {employee.last_name}"
        
        # Update allowed fields only
        if 'first_name' in data:
            employee.first_name = data['first_name'].upper()
        if 'last_name' in data:
            employee.last_name = data['last_name'].upper()
        
        with transaction.atomic():
            employee.save()
            
            # Create audit log
            after_data = f"Name: {employee.first_name} {employee.last_name}"
            
            create_audit_log(
                request.user,
                f'Employee Updated: {employee.employee_id}',
                f'Before: {before_data}, After: {after_data}',
                request
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Employee updated successfully',
            'employee': {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'full_name': employee.full_name
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
@require_http_methods(["PATCH"])
def deactivate_employee(request, employee_id):
    """Deactivate employee account"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    if employee.status == 'inactive':
        return JsonResponse({'success': False, 'error': 'Employee already inactive'}, status=400)
    
    try:
        with transaction.atomic():
            # Store before data
            before_data = f"Status: {employee.status}"
            
            # Deactivate employee
            employee.status = 'inactive'
            employee.save()
            
            # Create audit log
            after_data = f"Status: {employee.status}"
            create_audit_log(
                request.user,
                f'Employee Deactivated: {employee.employee_id}',
                f'Before: {before_data}, After: {after_data}',
                request
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Employee {employee.employee_id} has been deactivated'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def employee_attendance_history(request, employee_id):
    """Employee-wise attendance history view"""
    employee = get_object_or_404(CustomUser, employee_id=employee_id, role='field_officer')
    
    # Default date range (today)
    today = timezone.localdate()
    start_date = request.GET.get('start_date', today.isoformat())
    end_date = request.GET.get('end_date', today.isoformat())
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = end_date = today
    
    # Validate date range
    if start_date > end_date:
        messages.error(request, 'Start date cannot be after end date.')
        start_date = end_date = today
    
    # Get attendance records for the employee
    attendance_records = Attendance.objects.filter(
        user=employee,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Add late flag and location parsing
    from datetime import time
    for record in attendance_records:
        record.is_late = record.check_in_time and record.check_in_time > time(9, 30)
        if record.location and ',' in record.location:
            try:
                coords = record.location.split(',')
                record.latitude = float(coords[0].strip())
                record.longitude = float(coords[1].strip())
            except (ValueError, IndexError):
                record.latitude = record.longitude = None
        else:
            record.latitude = record.longitude = None
    
    # Pagination
    paginator = Paginator(attendance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Create audit log
    create_audit_log(
        request.user,
        f'Viewed Attendance History: {employee_id}',
        f'Date Range: {start_date} to {end_date}',
        request
    )
    
    context = {
        'employee': employee,
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'total_records': attendance_records.count(),
    }
    
    return render(request, 'authe/admin_employee_attendance_history.html', context)

@login_required
@admin_required
def attendance_daily(request):
    """Daily attendance grid view with monthly calendar - Query-Level Override for Approved Leave"""
    from calendar import monthrange
    
    # Get month/year from request or default to current
    today = timezone.localdate()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Get filters
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Get all days in the month
    _, days_in_month = monthrange(year, month)
    month_dates = [date(year, month, day) for day in range(1, days_in_month + 1)]
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', status='active').order_by('employee_id')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Get all attendance records for the month
    attendance_records = Attendance.objects.filter(
        date__year=year,
        date__month=month,
        user__in=employees
    ).select_related('user')
    
    # Create attendance lookup dict
    attendance_dict = {}
    for record in attendance_records:
        key = f"{record.user.employee_id}_{record.date}"
        attendance_dict[key] = record
    
    # Get approved leave records for the month (PRIORITY OVERRIDE)
    approved_leaves = LeaveRequest.objects.filter(
        status='approved',
        user__in=employees,
        start_date__lte=date(year, month, days_in_month),
        end_date__gte=date(year, month, 1)
    ).select_related('user')
    
    # Create leave lookup dict
    leave_dict = {}
    for leave in approved_leaves:
        current_date = max(leave.start_date, date(year, month, 1))
        end_date = min(leave.end_date, date(year, month, days_in_month))
        
        while current_date <= end_date:
            if current_date.weekday() != 6:  # Skip Sundays
                key = f"{leave.user.employee_id}_{current_date}"
                leave_dict[key] = {
                    'leave': leave,
                    'status': 'leave_full' if leave.duration == 'full_day' else 'leave_half'
                }
            current_date += timedelta(days=1)
    
    # Get holidays for the month
    holidays = Holiday.objects.filter(
        date__year=year,
        date__month=month
    ).values_list('date', flat=True)
    holiday_dates = set(holidays)
    
    # Build employee data with PRIORITY LOGIC: Leave > Attendance > Not Marked
    employee_data = []
    for employee in employees:
        daily_attendance = []
        for day_date in month_dates:
            key = f"{employee.employee_id}_{day_date}"
            
            # Check if it's a holiday or Sunday
            is_holiday = day_date in holiday_dates or day_date.weekday() == 6
            
            # PRIORITY 1: Check for approved leave (OVERRIDE)
            if key in leave_dict:
                leave_data = leave_dict[key]
                daily_attendance.append({
                    'date': day_date,
                    'attendance': None,
                    'leave': leave_data['leave'],
                    'status': leave_data['status'],
                    'is_holiday': is_holiday,
                    'is_late': False,
                    'is_leave': True
                })
            # PRIORITY 2: Check for attendance record
            elif key in attendance_dict:
                attendance = attendance_dict[key]
                daily_attendance.append({
                    'date': day_date,
                    'attendance': attendance,
                    'leave': None,
                    'status': attendance.status,
                    'is_holiday': is_holiday,
                    'is_late': hasattr(attendance, 'check_in_time') and attendance.check_in_time and attendance.check_in_time > time(9, 30),
                    'is_leave': False
                })
            # PRIORITY 3: Not marked
            else:
                daily_attendance.append({
                    'date': day_date,
                    'attendance': None,
                    'leave': None,
                    'status': 'not_marked',
                    'is_holiday': is_holiday,
                    'is_late': False,
                    'is_leave': False
                })
        
        employee_data.append({
            'employee': employee,
            'daily_attendance': daily_attendance
        })
    
    context = {
        'employee_data': employee_data,
        'month_dates': month_dates,
        'selected_month': month,
        'selected_year': year,
        'month_name': date(year, month, 1).strftime('%B'),
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'today': today,
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
    """Leave approval workflow with admin remarks"""
    status_filter = request.GET.get('status', 'pending')
    
    leaves = LeaveRequest.objects.filter(status=status_filter).select_related('user', 'approved_by').order_by('-applied_at')
    
    # Pagination
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    }
    
    return render(request, 'authe/admin_leave_requests.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def decide_leave(request, leave_id):
    """Approve or reject leave request with admin remarks"""
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
            
            # Update leave request with admin remarks
            leave_request.status = 'approved' if action == 'approve' else 'rejected'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.admin_remarks = admin_remarks
            
            leave_request.save()
            
            # Note: No longer auto-creating attendance records for approved leave
            # Leave status is now handled via query-level override in attendance views
            
            # Create audit log
            after_data = f"Status: {leave_request.status}, Remarks: {admin_remarks}"
            create_audit_log(
                request.user,
                f'Leave Request {action.title()}d: {leave_request.id}',
                f'Employee: {leave_request.user.employee_id}, Before: {before_data}, After: {after_data}',
                request
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Leave request {action}d successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
def compact_analytics_api(request):
    """API for compact analytics dashboard"""
    today = timezone.localdate()
    
    # Get active employees
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    total_employees = employees.count()
    
    # Get today's attendance
    attendance_records = Attendance.objects.filter(date=today).select_related('user')
    attendance_dict = {att.user.employee_id: att for att in attendance_records}
    
    # DCCB-wise data
    dccb_data = []
    for dccb_code, dccb_name in CustomUser.DCCB_CHOICES:
        dccb_employees = employees.filter(dccb=dccb_code)
        if dccb_employees.exists():
            dccb_stats = {'name': dccb_name, 'present': 0, 'absent': 0, 'half_day': 0, 'not_marked': 0}
            
            for emp in dccb_employees:
                att = attendance_dict.get(emp.employee_id)
                if att:
                    if att.status == 'present':
                        dccb_stats['present'] += 1
                    elif att.status == 'absent':
                        dccb_stats['absent'] += 1
                    elif att.status == 'half_day':
                        dccb_stats['half_day'] += 1
                else:
                    dccb_stats['not_marked'] += 1
            
            dccb_data.append(dccb_stats)
    
    # Overall summary
    present_count = sum(1 for att in attendance_records if att.status == 'present')
    absent_count = sum(1 for att in attendance_records if att.status == 'absent')
    half_day_count = sum(1 for att in attendance_records if att.status == 'half_day')
    not_marked_count = total_employees - len(attendance_records)
    
    # Late vs On-time
    late_count = sum(1 for att in attendance_records if att.status == 'present' and att.check_in_time and att.check_in_time > time(9, 30))
    on_time_count = present_count - late_count
    
    # Marking completion
    marked_count = len(attendance_records)
    marking_percentage = round((marked_count / total_employees * 100), 1) if total_employees > 0 else 0
    
    return JsonResponse({
        'dccb_data': dccb_data,
        'summary': {
            'present': present_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'not_marked': not_marked_count,
            'total_employees': total_employees,
            'attendance_percentage': round((present_count / total_employees * 100), 1) if total_employees > 0 else 0
        },
        'punctuality': {
            'on_time': on_time_count,
            'late': late_count
        },
        'completion': {
            'marked': marked_count,
            'not_marked': not_marked_count,
            'percentage': marking_percentage
        }
    })

@login_required
@admin_required
def compact_analytics_dashboard(request):
    """Compact analytics dashboard view"""
    return render(request, 'authe/admin_compact_analytics.html')

@login_required
@admin_required
def reports_analytics(request):
    """Clean, compact analytics dashboard"""
    from datetime import time
    
    # Get last 30 days data
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=30)
    
    # Active employees
    employees = CustomUser.objects.filter(role='field_officer', status='active')
    total_employees = employees.count()
    
    # Attendance data for period
    attendance_qs = Attendance.objects.filter(
        user__in=employees,
        date__range=[start_date, end_date]
    ).select_related('user')
    
    total_days = 30
    total_possible = total_employees * total_days
    
    # Calculate KPIs
    present_count = attendance_qs.filter(status='present').count()
    absent_count = attendance_qs.filter(status='absent').count()
    half_day_count = attendance_qs.filter(status='half_day').count()
    late_count = attendance_qs.filter(status='present', check_in_time__gt=time(9, 30)).count()
    marked_count = present_count + absent_count + half_day_count
    not_marked = total_possible - marked_count
    
    kpis = {
        'attendance_rate': round((present_count + half_day_count) / total_possible * 100, 1) if total_possible > 0 else 0,
        'absenteeism_rate': round(absent_count / total_possible * 100, 1) if total_possible > 0 else 0,
        'late_arrival_rate': round(late_count / present_count * 100, 1) if present_count > 0 else 0,
        'total_employees': total_employees
    }
    
    context = {
        'kpis': kpis,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'authe/admin_reports_analytics.html', context)

@login_required
@admin_required
def analytics_data(request):
    """Simplified analytics data API"""
    from datetime import time
    
    chart_type = request.GET.get('type', 'trend')
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=30)
    
    employees = CustomUser.objects.filter(role='field_officer', status='active')
    attendance_qs = Attendance.objects.filter(
        user__in=employees,
        date__range=[start_date, end_date]
    ).select_related('user')
    
    if chart_type == 'trend':
        # Daily trend data (last 30 days)
        data = []
        current_date = start_date
        while current_date <= end_date:
            day_data = attendance_qs.filter(date=current_date)
            data.append({
                'date': current_date.strftime('%m-%d'),
                'present': day_data.filter(status='present').count(),
                'absent': day_data.filter(status='absent').count()
            })
            current_date += timedelta(days=1)
        return JsonResponse({'data': data})
    
    elif chart_type == 'distribution':
        # Status distribution
        present = attendance_qs.filter(status='present').count()
        absent = attendance_qs.filter(status='absent').count()
        half_day = attendance_qs.filter(status='half_day').count()
        not_marked = (employees.count() * 30) - (present + absent + half_day)
        
        return JsonResponse({
            'data': [
                {'label': 'Present', 'value': present, 'color': '#10b981'},
                {'label': 'Absent', 'value': absent, 'color': '#ef4444'},
                {'label': 'Half Day', 'value': half_day, 'color': '#f59e0b'},
                {'label': 'Not Marked', 'value': not_marked, 'color': '#6b7280'}
            ]
        })
    
    elif chart_type == 'late_arrival':
        # Late arrival distribution
        from datetime import time
        present_records = attendance_qs.filter(status='present')
        on_time = present_records.filter(check_in_time__lte=time(9, 30)).count()
        late = present_records.filter(check_in_time__gt=time(9, 30)).count()
        
        return JsonResponse({
            'data': [
                {'label': 'On-time', 'value': on_time, 'color': '#10b981'},
                {'label': 'Late', 'value': late, 'color': '#f59e0b'}
            ]
        })
    
    elif chart_type == 'dccb':
        # DCCB comparison (top 5 only)
        dccb_data = []
        for dccb_code, dccb_name in CustomUser.DCCB_CHOICES[:5]:
            dccb_employees = employees.filter(dccb=dccb_code)
            if dccb_employees.exists():
                dccb_attendance = attendance_qs.filter(user__dccb=dccb_code)
                present_count = dccb_attendance.filter(status='present').count() + dccb_attendance.filter(status='half_day').count()
                total_possible = dccb_employees.count() * 30
                percentage = round(present_count / total_possible * 100, 1) if total_possible > 0 else 0
                
                dccb_data.append({
                    'name': dccb_name,
                    'percentage': percentage,
                    'count': present_count,
                    'total': total_possible
                })
        
        return JsonResponse({'data': sorted(dccb_data, key=lambda x: x['percentage'], reverse=True)})

@login_required
@admin_required
def attendance_geo_data(request):
    """Get attendance geo data for map display with filters"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    status_filter = request.GET.get('status', '')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    # Get attendance records with location data for the selected date
    attendance_records = Attendance.objects.select_related('user').filter(
        date=selected_date,
        location__isnull=False
    ).exclude(location='')
    
    # Apply status filter if provided
    if status_filter:
        attendance_records = attendance_records.filter(status=status_filter)
    
    geo_data = []
    for record in attendance_records:
        if record.location and ',' in record.location:
            try:
                coords = record.location.split(',')
                lat, lng = float(coords[0].strip()), float(coords[1].strip())
                
                # Determine if late
                is_late = False
                if record.check_in_time:
                    from datetime import time
                    is_late = record.check_in_time > time(9, 30)
                
                geo_data.append({
                    'employee_id': record.user.employee_id,
                    'name': record.user.full_name,
                    'designation': record.user.designation,
                    'dccb': record.user.dccb or 'N/A',
                    'status': record.status,
                    'is_late': is_late,
                    'lat': lat,
                    'lng': lng,
                    'marked_at': record.marked_at.strftime('%d-%b-%Y %H:%M') if record.marked_at else 'N/A'
                })
            except (ValueError, IndexError):
                continue
    
    return JsonResponse(geo_data, safe=False)

@login_required
@admin_required
def attendance_geo(request):
    """Geo-location map view with OpenLayers"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    status_filter = request.GET.get('status', '')
    
    context = {
        'selected_date': selected_date,
        'status_filter': status_filter,
    }
    
    # Add debug info to context
    context['debug_info'] = {
        'total_attendance': Attendance.objects.filter(date=selected_date).count(),
        'with_location': Attendance.objects.filter(date=selected_date, location__isnull=False).exclude(location='').count()
    }
    
    return render(request, 'authe/admin_attendance_geo_working.html', context)

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
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        employees = employees.filter(status=status_filter)
    
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
                emp.full_name,
                emp.designation,
                emp.contact_number,
                emp.dccb or '',
                emp.reporting_manager or '',
                emp.registration_at.strftime('%Y-%m-%d %H:%M:%S'),
                emp.get_status_display()
            ])
        
        return response
    
    # Add other export formats (PDF, XLSX) here
    return JsonResponse({'error': 'Format not supported'}, status=400)

@login_required
@admin_required
def export_monthly_attendance(request):
    """Export monthly attendance report"""
    from calendar import monthrange
    
    month = int(request.GET.get('month', timezone.localdate().month))
    year = int(request.GET.get('year', timezone.localdate().year))
    format_type = request.GET.get('format', 'csv')
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', status='active')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Get attendance data for the month
    attendance_records = Attendance.objects.filter(
        date__year=year,
        date__month=month,
        user__in=employees
    ).select_related('user')
    
    # Calculate stats per employee
    employee_stats = {}
    for emp in employees:
        employee_stats[emp.employee_id] = {
            'employee': emp,
            'present': 0,
            'absent': 0,
            'half_day': 0,
            'not_marked': 0
        }
    
    for record in attendance_records:
        emp_id = record.user.employee_id
        if emp_id in employee_stats:
            if record.status == 'present':
                employee_stats[emp_id]['present'] += 1
            elif record.status == 'absent':
                employee_stats[emp_id]['absent'] += 1
            elif record.status == 'half_day':
                employee_stats[emp_id]['half_day'] += 1
    
    # Calculate not marked days
    _, days_in_month = monthrange(year, month)
    for emp_id, stats in employee_stats.items():
        marked_days = stats['present'] + stats['absent'] + stats['half_day']
        stats['not_marked'] = days_in_month - marked_days
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="monthly_attendance_{year}_{month:02d}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([f'Monthly Attendance Report - {date(year, month, 1).strftime("%B %Y")}'])
        writer.writerow([f'Total Employees: {len(employee_stats)}'])
        writer.writerow([])
        
        writer.writerow(['Employee ID', 'Full Name', 'DCCB', 'Present', 'Absent', 'Half Day', 'Not Marked'])
        
        for stats in employee_stats.values():
            emp = stats['employee']
            writer.writerow([
                emp.employee_id,
                emp.full_name,
                emp.dccb or '',
                stats['present'],
                stats['absent'],
                stats['half_day'],
                stats['not_marked']
            ])
        
        return response
    
    return JsonResponse({'error': 'Format not supported'}, status=400)

@login_required
@admin_required
def export_dccb_summary(request):
    """Export DCCB-wise summary"""
    from calendar import monthrange
    
    month = int(request.GET.get('month', timezone.localdate().month))
    year = int(request.GET.get('year', timezone.localdate().year))
    format_type = request.GET.get('format', 'csv')
    
    # Get DCCB-wise stats
    dccb_stats = {}
    for dccb_code, dccb_name in CustomUser.DCCB_CHOICES:
        employees = CustomUser.objects.filter(role='field_officer', status='active', dccb=dccb_code)
        total_employees = employees.count()
        
        if total_employees > 0:
            attendance_records = Attendance.objects.filter(
                date__year=year,
                date__month=month,
                user__in=employees
            )
            
            present = attendance_records.filter(status='present').count()
            absent = attendance_records.filter(status='absent').count()
            half_day = attendance_records.filter(status='half_day').count()
            
            _, days_in_month = monthrange(year, month)
            total_possible = total_employees * days_in_month
            marked = present + absent + half_day
            not_marked = total_possible - marked
            
            dccb_stats[dccb_name] = {
                'present': present,
                'absent': absent,
                'half_day': half_day,
                'not_marked': not_marked,
                'total_employees': total_employees
            }
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="dccb_summary_{year}_{month:02d}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([f'DCCB-wise Summary - {date(year, month, 1).strftime("%B %Y")}'])
        writer.writerow([])
        
        writer.writerow(['DCCB', 'Present', 'Absent', 'Half Day', 'Not Marked', 'Total Employees'])
        
        for dccb_name, stats in dccb_stats.items():
            writer.writerow([
                dccb_name,
                stats['present'],
                stats['absent'],
                stats['half_day'],
                stats['not_marked'],
                stats['total_employees']
            ])
        
        return response
    
    return JsonResponse({'error': 'Format not supported'}, status=400)

@login_required
@admin_required
def export_date_range_attendance(request):
    """Export attendance report for date range"""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    format_type = request.GET.get('format', 'csv')
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    if not from_date or not to_date:
        return JsonResponse({'error': 'From date and to date are required'}, status=400)
    
    try:
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', status='active')
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        date__range=[from_date, to_date],
        user__in=employees
    ).select_related('user')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_range_{from_date}_{to_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([f'Attendance Report - {from_date} to {to_date}'])
        writer.writerow([f'Total Employees: {employees.count()}'])
        writer.writerow([])
        
        writer.writerow(['Employee ID', 'Full Name', 'DCCB', 'Date', 'Status', 'Check In', 'Check Out', 'Arrival Status', 'Latitude', 'Longitude', 'Location', 'Google Maps Link'])
        
        for record in attendance_records.order_by('user__employee_id', 'date'):
            # Determine arrival status
            arrival_status = 'Not Marked'
            if record.check_in_time:
                if record.check_in_time <= time(9, 30):
                    arrival_status = 'On Time'
                else:
                    arrival_status = 'Late Arrival'
            
            # Create Google Maps link if coordinates exist
            maps_link = ''
            if hasattr(record, 'latitude') and hasattr(record, 'longitude') and record.latitude and record.longitude:
                maps_link = f'https://maps.google.com/?q={record.latitude},{record.longitude}'
            
            writer.writerow([
                record.user.employee_id,
                record.user.full_name,
                record.user.dccb or '',
                record.date.strftime('%Y-%m-%d'),
                record.get_status_display(),
                record.check_in_time.strftime('%H:%M') if record.check_in_time else '',
                record.check_out_time.strftime('%H:%M') if record.check_out_time else '',
                arrival_status,
                getattr(record, 'latitude', '') or '',
                getattr(record, 'longitude', '') or '',
                record.location or '',
                maps_link
            ])
        
        return response
    
    return JsonResponse({'error': 'Format not supported'}, status=400)

@login_required
@admin_required
def notifications_api(request):
    """API to fetch notifications for admin users"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor').order_by('-created_at')[:15]
    
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id,
            'actor_id': notification.actor.employee_id,
            'actor_name': notification.actor.full_name,
            'event_type': notification.event_type,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d %b %Y, %I:%M %p'),
            'reference_id': notification.reference_id
        })
    
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    return JsonResponse({
        'notifications': data,
        'unread_count': unread_count
    })

@login_required
@admin_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        # Determine redirect URL based on event type
        redirect_url = '/admin/dashboard/'
        if notification.event_type == 'LEAVE_REQUEST':
            redirect_url = '/admin/leave-requests/'
        elif notification.event_type == 'ATTENDANCE_MARKED':
            redirect_url = '/admin/attendance/daily/'
        
        return JsonResponse({
            'success': True,
            'redirect_url': redirect_url
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@admin_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current admin user"""
    try:
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count} notifications marked as read'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)