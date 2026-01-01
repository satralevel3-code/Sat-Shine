from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date
from .models import CustomUser, Attendance, LeaveRequest, AuditLog, Holiday
import json
import csv
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
    if status_filter:
        employees = employees.filter(status=status_filter)
    
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
        'status_choices': CustomUser.STATUS_CHOICES,
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
def attendance_daily(request):
    """Daily attendance grid view"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    
    # Get employees
    employees = CustomUser.objects.filter(role='field_officer', is_active=True)
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    
    # Get attendance for the date
    attendance_records = Attendance.objects.filter(date=selected_date).select_related('user')
    attendance_dict = {att.user.employee_id: att for att in attendance_records}
    
    # Check if date is holiday
    is_holiday = Holiday.objects.filter(date=selected_date).exists() or selected_date.weekday() == 6  # Sunday
    
    # Prepare employee data with attendance
    employee_data = []
    for employee in employees:
        attendance = attendance_dict.get(employee.employee_id)
        employee_data.append({
            'employee': employee,
            'attendance': attendance,
            'status': attendance.status if attendance else 'Not Marked',
            'marked_at': attendance.marked_at if attendance else None
        })
    
    context = {
        'employee_data': employee_data,
        'selected_date': selected_date,
        'is_holiday': is_holiday,
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
    """Leave approval workflow"""
    status_filter = request.GET.get('status', 'pending')
    
    leaves = LeaveRequest.objects.filter(status=status_filter).select_related('user').order_by('-applied_at')
    
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
    """Approve or reject leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    
    if leave_request.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Leave request already processed'}, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'reject'
        comments = data.get('admin_comments', '')
        
        if action not in ['approve', 'reject']:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        with transaction.atomic():
            # Store before data
            before_data = f"Status: {leave_request.status}"
            
            # Update leave request
            leave_request.status = 'approved' if action == 'approve' else 'rejected'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            # Create audit log
            after_data = f"Status: {leave_request.status}"
            create_audit_log(
                request.user,
                f'Leave Request {action.title()}d: {leave_request.id}',
                f'Before: {before_data}, After: {after_data}',
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
def attendance_geo(request):
    """Geo-location map view of attendance"""
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()
    
    dccb_filter = request.GET.get('dccb', '')
    designation_filter = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    
    # Get attendance records with valid coordinates
    attendance_records = Attendance.objects.filter(
        date=selected_date,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('user')
    
    # Apply filters
    if dccb_filter:
        attendance_records = attendance_records.filter(user__dccb=dccb_filter)
    if designation_filter:
        attendance_records = attendance_records.filter(user__designation=designation_filter)
    if status_filter:
        attendance_records = attendance_records.filter(code=status_filter)
    
    # Prepare geo data
    geo_data = []
    for record in attendance_records:
        geo_data.append({
            'employee_id': record.user.employee_id,
            'name': record.user.full_name,
            'designation': record.user.designation,
            'dccb': record.user.dccb,
            'status': record.code,
            'status_display': record.status_display,
            'is_late': record.late_flag,
            'marked_at': record.marked_at.strftime('%H:%M') if record.marked_at else '',
            'latitude': float(record.latitude),
            'longitude': float(record.longitude),
            'address': record.reverse_geocode_address or ''
        })
    
    context = {
        'geo_data': json.dumps(geo_data),
        'selected_date': selected_date,
        'dccb_filter': dccb_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'status_choices': Attendance.STATUS_CHOICES,
    }
    
    return render(request, 'authe/admin_attendance_geo.html', context)

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