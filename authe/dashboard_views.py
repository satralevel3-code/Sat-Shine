from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, time
from .models import CustomUser, Attendance, LeaveRequest
from .views import create_audit_log
import json
import os

# Conditional GIS imports
if os.getenv('USE_POSTGRESQL', 'false').lower() == 'true':
    try:
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import Distance
        GIS_ENABLED = True
    except ImportError:
        GIS_ENABLED = False
else:
    GIS_ENABLED = False

@login_required
def field_dashboard(request):
    """Main dashboard for field officers - role-based access"""
    if request.user.role != 'field_officer':
        messages.error(request, 'Access denied. Field Officer privileges required.')
        return redirect('admin_dashboard')
    
    # Clear all messages on dashboard load to prevent persistence
    storage = messages.get_messages(request)
    storage.used = True
    
    # Get today's attendance
    today = timezone.localdate()
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    # Get recent attendance (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(
        user=request.user, 
        date__gte=week_ago
    ).order_by('-date')[:7]
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.objects.filter(
        user=request.user, 
        status='pending'
    ).count()
    
    # Get recent leave requests for display
    recent_leaves = LeaveRequest.objects.filter(
        user=request.user
    ).order_by('-applied_at')[:5]
    
    # Check if user can view team data (DC only)
    can_view_team = request.user.designation == 'DC'
    team_data = None
    team_members = []  # Initialize team_members
    
    if can_view_team:
        # Get team attendance for DC
        team_users = CustomUser.objects.filter(
            role='field_officer',
            dccb=request.user.dccb,
            designation__in=['MT', 'Support']
        ).exclude(id=request.user.id).order_by('employee_id')
        
        # Get today's attendance for team members
        team_members = []
        for user in team_users:
            user_attendance = Attendance.objects.filter(user=user, date=today).first()
            user.today_attendance = user_attendance
            team_members.append(user)
        
        team_attendance_today = Attendance.objects.filter(
            user__in=team_users,
            date=today
        ).values('status').annotate(count=Count('status'))
        
        team_data = {
            'total_team': team_users.count(),
            'attendance_summary': {item['status']: item['count'] for item in team_attendance_today}
        }
    
    context = {
        'user': request.user,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'recent_leaves': recent_leaves,
        'can_view_team': can_view_team,
        'team_data': team_data,
        'team_members': team_members,
        'current_time': timezone.now(),
    }
    
    return render(request, 'authe/field_dashboard.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST", "GET"])
def mark_attendance(request):
    """Production-ready attendance marking with high-accuracy GPS validation"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.localdate()
    is_sunday_today = today.weekday() == 6
    
    if request.method == 'POST':
        if is_sunday_today:
            return JsonResponse({
                'success': False, 
                'error': 'Attendance marking not allowed on Sundays'
            }, status=400)
            
        try:
            data = json.loads(request.body)
            latitude = data.get('lat')
            longitude = data.get('lng')
            accuracy = data.get('accuracy')
            timestamp = data.get('timestamp')
            
            current_time = timezone.localtime().time()
            
            # Check if already marked
            existing = Attendance.objects.filter(user=request.user, date=today).first()
            if existing:
                return JsonResponse({'success': False, 'error': 'Attendance already marked for today'}, status=400)
            
            # Strict backend validation of GPS accuracy
            is_location_valid = False
            if latitude is not None and longitude is not None and accuracy is not None:
                try:
                    lat_float = float(latitude)
                    lng_float = float(longitude)
                    acc_float = float(accuracy)
                    
                    # Validate coordinate ranges
                    if not (-90 <= lat_float <= 90 and -180 <= lng_float <= 180):
                        return JsonResponse({
                            'success': False, 
                            'error': 'Invalid GPS coordinates received'
                        }, status=400)
                    
                    # Strict accuracy validation - reject if > 50m
                    if acc_float > 50:
                        return JsonResponse({
                            'success': False, 
                            'error': f'GPS accuracy too low ({acc_float:.0f}m). Required: ≤50m accuracy'
                        }, status=400)
                    
                    is_location_valid = True
                    
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid location data format'
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'GPS location required for attendance marking'
                }, status=400)
            
            # Time-based attendance rules
            on_time_cutoff = time(10, 0)
            late_cutoff = time(13, 30)
            half_day_cutoff = time(15, 0)
            
            if current_time <= on_time_cutoff:
                status = 'present'
                timing_status = 'On Time'
                message = 'Attendance marked successfully - On Time'
            elif current_time <= late_cutoff:
                status = 'present'
                timing_status = 'Late Arrival'
                message = f'Marked late at {current_time.strftime("%I:%M %p")} - Late Arrival'
            elif current_time <= half_day_cutoff:
                status = 'half_day'
                timing_status = 'Half Day'
                message = f'Marked at {current_time.strftime("%I:%M %p")} - Half Day'
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Attendance marking not allowed after 3:00 PM. Current time: {current_time.strftime("%I:%M %p")}'
                }, status=400)
            
            # Create attendance record with validated location
            attendance = Attendance.objects.create(
                user=request.user,
                date=today,
                status=status,
                check_in_time=current_time,
                check_in_location=f"{lat_float:.8f},{lng_float:.8f}",
                location_accuracy=acc_float,
                is_location_valid=is_location_valid,
                location_address='GPS Location Captured'
            )
            
            # Optional: Office geofencing validation (200m radius)
            if request.user.office_location:
                try:
                    if hasattr(request.user.office_location, 'coords'):
                        # GIS Point field
                        office_lat, office_lng = request.user.office_location.coords[1], request.user.office_location.coords[0]
                    elif ',' in str(request.user.office_location):
                        # String format
                        office_lat, office_lng = map(float, str(request.user.office_location).split(','))
                    else:
                        office_lat = office_lng = None
                    
                    if office_lat and office_lng:
                        # Calculate distance using Haversine formula
                        import math
                        lat_diff = math.radians(lat_float - office_lat)
                        lng_diff = math.radians(lng_float - office_lng)
                        a = math.sin(lat_diff/2)**2 + math.cos(math.radians(office_lat)) * math.cos(math.radians(lat_float)) * math.sin(lng_diff/2)**2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                        distance = 6371000 * c  # Earth radius in meters
                        
                        if distance > 200:  # 200m office radius
                            attendance.location_address = f'Outside office area ({distance:.0f}m from office)'
                        else:
                            attendance.location_address = f'Within office area ({distance:.0f}m from office)'
                        attendance.save()
                        
                except Exception:
                    pass  # Ignore geofencing errors
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='ATTENDANCE_MARKED',
                details=f'Status: {status}, Time: {current_time}, Location: {lat_float:.6f},{lng_float:.6f}'
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'timing_status': timing_status,
                'check_in_time': current_time.strftime('%I:%M %p'),
                'location': f'{lat_float:.6f},{lng_float:.6f}',
                'accuracy': f'{acc_float:.1f}m'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
    
    # GET request - return attendance form
    context = {
        'user': request.user,
        'today': today,
        'is_sunday': is_sunday_today,
        'current_time': timezone.now()
    }
    return render(request, 'authe/mark_attendance.html', context)ians(office_lat)) * math.cos(math.radians(lat_float)) * math.sin(lng_diff/2)**2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                        distance = 6371000 * c  # Earth radius in meters
                        
                        if distance > 200:  # 200m office radius
                            attendance.location_address = f'Outside office area ({distance:.0f}m from office)'
                        else:
                            attendance.location_address = f'Within office area ({distance:.0f}m from office)'
                        attendance.save()
                        
                except Exception:
                    pass  # Ignore geofencing errors
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='ATTENDANCE_MARKED',
                details=f'Status: {status}, Time: {current_time}, Location: {lat_float:.6f},{lng_float:.6f}'
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'timing_status': timing_status,
                'check_in_time': current_time.strftime('%I:%M %p'),
                'location': f'{lat_float:.6f},{lng_float:.6f}',
                'accuracy': f'{acc_float:.1f}m'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
    
    # GET request - return attendance form
    context = {
        'user': request.user,
        'today': today,
        'is_sunday': is_sunday_today,
        'current_time': timezone.now()
    }
    return render(request, 'authe/mark_attendance.html', context)
                        c = 2 * math.asin(math.sqrt(a))
                        distance = 6371000 * c  # Earth radius in meters
                        
                        attendance.distance_from_office = round(distance, 2)
                        
                        # Geofencing check (200m radius)
                        if distance > 200:
                            attendance.is_location_valid = False
                            message += f' (Outside office area: {distance:.0f}m)'
                        
                        attendance.save()
                except Exception as e:
                    print(f"Geofencing calculation error: {e}")
            
            # Create audit log
            create_audit_log(
                request.user,
                'Attendance Marked',
                request,
                f'Status: {status}, Timing: {timing_status}, GPS: {lat_float:.6f},{lng_float:.6f}, Accuracy: {acc_float}m'
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'attendance': {
                    'status': attendance.status,
                    'check_in_time': attendance.check_in_time.strftime('%I:%M %p'),
                    'timing_status': timing_status,
                    'accuracy': f'{acc_float:.0f}m',
                    'location_valid': is_location_valid
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request format'}, status=400)
        except Exception as e:
            print(f"Attendance marking error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Server error occurred'}, status=500)
    
    # GET request - show the mark attendance page
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    context = {
        'user': request.user,
        'today_attendance': today_attendance,
        'current_time': timezone.now(),
        'is_sunday': is_sunday_today,
    }
    
    return render(request, 'authe/mark_attendance.html', context)

@login_required
def attendance_summary(request):
    """Get attendance summary for date range"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    else:
        # Default to current month
        today = timezone.localdate()
        start_date = today.replace(day=1)
        # Get last day of month
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    # Get attendance records in date range
    attendance_records = Attendance.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    )
    
    # Count by status
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count() + attendance_records.filter(status='auto_not_marked').count()
    half_day_count = attendance_records.filter(status='half_day').count()
    total_days = (end_date - start_date).days + 1
    
    return JsonResponse({
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'present': present_count,
        'absent': absent_count,
        'half_day': half_day_count,
        'total_days': total_days
    })

@login_required
def attendance_history(request):
    """View attendance history"""
    if request.user.role != 'field_officer':
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    
    # Get current month by default
    today = timezone.localdate()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Get attendance for the month
    attendance_records = Attendance.objects.filter(
        user=request.user,
        date__month=month,
        date__year=year
    ).order_by('date')
    
    context = {
        'attendance_records': attendance_records,
        'current_month': month,
        'current_year': year,
        'user': request.user,
    }
    
    return render(request, 'authe/attendance_history.html', context)

@login_required
def apply_leave(request):
    """Apply for leave"""
    if request.user.role != 'field_officer':
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        duration = request.POST.get('duration', 'full_day')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        days_requested = request.POST.get('days_requested')
        reason = request.POST.get('reason', '').strip()
        
        # Validation
        if not all([leave_type, start_date, end_date, reason]):
            messages.error(request, 'All fields are required.')
            return render(request, 'authe/apply_leave.html')
        
        if len(reason.split()) < 5:
            messages.error(request, 'Reason must be at least 5 words.')
            return render(request, 'authe/apply_leave.html')
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            days_requested = float(days_requested)
        except ValueError:
            messages.error(request, 'Invalid date or days format.')
            return render(request, 'authe/apply_leave.html')
        
        if start_date > end_date:
            messages.error(request, 'Start date cannot be after end date.')
            return render(request, 'authe/apply_leave.html')
        
        # Business rule validation: Planned leave cannot be for past dates
        today = timezone.localdate()
        if leave_type == 'planned' and start_date < today:
            messages.error(request, 'Planned leave cannot be applied for past dates.')
            return render(request, 'authe/apply_leave.html')
        
        if start_date < timezone.localdate() and leave_type == 'planned':
            messages.error(request, 'Cannot apply planned leave for past dates.')
            return render(request, 'authe/apply_leave.html')
        
        # Create leave request
        leave_request = LeaveRequest.objects.create(
            user=request.user,
            leave_type=leave_type,
            duration=duration,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason
        )
        
        # Create audit log
        create_audit_log(
            request.user,
            'Leave Request Applied',
            request,
            f'Type: {leave_type}, Duration: {duration}, Days: {days_requested}'
        )
        
        messages.success(request, 'Leave request sent for approval.')
        return redirect('field_dashboard')
    
    # Get user's leave requests for display
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-applied_at')[:10]
    
    context = {
        'leave_requests': leave_requests,
        'user': request.user,
    }
    
    return render(request, 'authe/apply_leave.html', context)

@login_required
def team_attendance(request):
    """View team attendance - DC only"""
    if request.user.role != 'field_officer' or request.user.designation != 'DC':
        messages.error(request, 'Access denied. DC privileges required.')
        return redirect('field_dashboard')
    
    # Get team members (MT & Support in same DCCB)
    team_users = CustomUser.objects.filter(
        role='field_officer',
        dccb=request.user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=request.user.id)
    
    # Get date range
    today = timezone.localdate()
    start_date = request.GET.get('start_date', today.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = end_date = today
    
    # Get attendance data
    attendance_data = Attendance.objects.filter(
        user__in=team_users,
        date__range=[start_date, end_date]
    ).select_related('user').order_by('-date', 'user__employee_id')
    
    # Filter by user if specified
    user_filter = request.GET.get('user_filter')
    if user_filter:
        attendance_data = attendance_data.filter(user__employee_id=user_filter)
    
    # Filter by status if specified
    status_filter = request.GET.get('status_filter')
    if status_filter:
        attendance_data = attendance_data.filter(status=status_filter)
    
    context = {
        'team_users': team_users,
        'attendance_data': attendance_data,
        'start_date': start_date,
        'end_date': end_date,
        'user_filter': user_filter,
        'status_filter': status_filter,
        'user': request.user,
    }
    
    return render(request, 'authe/team_attendance.html', context)

@login_required
def ping_employee(request):
    """Send notification to team member who hasn't marked attendance"""
    if request.user.role != 'field_officer' or request.user.designation != 'DC':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        name = data.get('name')
        dccb = data.get('dccb')
        
        # Verify the employee is under this DC's supervision
        try:
            employee = CustomUser.objects.get(
                employee_id=employee_id,
                role='field_officer',
                dccb=request.user.dccb,
                designation__in=['MT', 'Support']
            )
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Employee not found or access denied'}, status=404)
        
        # Check if employee has already marked attendance today
        today = timezone.localdate()
        existing_attendance = Attendance.objects.filter(user=employee, date=today).first()
        if existing_attendance:
            return JsonResponse({'error': 'Employee has already marked attendance'}, status=400)
        
        # Create audit log for ping action
        create_audit_log(
            request.user,
            'Employee Pinged',
            request,
            f'Pinged {name} ({employee_id}) from {dccb} for attendance'
        )
        
        # In a real implementation, you would send actual notification here
        # For now, we'll just log it and return success
        # Example: send_notification(employee.email, employee.contact_number, message)
        
        return JsonResponse({
            'success': True,
            'message': f'Notification sent to {name} ({employee_id})'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)