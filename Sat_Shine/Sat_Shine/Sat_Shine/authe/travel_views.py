from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date
from .models import CustomUser, TravelRequest
import json
import csv

@login_required
def get_associate_for_dccb(request):
    """Get Associate name for current user's DCCB"""
    user_dccb = request.user.dccb
    
    # Get all Associates and check their multiple_dccb field
    associates = CustomUser.objects.filter(
        designation='Associate',
        is_active=True
    )
    
    for assoc in associates:
        if assoc.multiple_dccb and user_dccb in assoc.multiple_dccb:
            return JsonResponse({
                'success': True,
                'associate_name': f"{assoc.first_name} {assoc.last_name}",
                'associate_id': assoc.employee_id
            })
    
    return JsonResponse({
        'success': False,
        'error': f'No Associate found for DCCB: {user_dccb}'
    })

@login_required
def travel_request_dashboard(request):
    """Travel request dashboard for MT, DC, Support"""
    if request.user.designation not in ['MT', 'DC', 'Support']:
        messages.error(request, 'Access denied. Travel requests only for MT, DC, Support.')
        return redirect('field_dashboard')
    
    # Get pending travel requests count
    pending_count = TravelRequest.objects.filter(
        user=request.user,
        status='pending'
    ).count()
    
    # Get date range for filtering
    from_date = request.GET.get('from_date', timezone.localdate().isoformat())
    to_date = request.GET.get('to_date', (timezone.localdate() + timedelta(days=30)).isoformat())
    
    # Get travel requests for the user
    travel_requests = TravelRequest.objects.filter(
        user=request.user,
        from_date__range=[from_date, to_date]
    ).order_by('-created_at')
    
    context = {
        'pending_count': pending_count,
        'travel_requests': travel_requests,
        'from_date': from_date,
        'to_date': to_date,
    }
    
    return render(request, 'authe/travel_request_dashboard.html', context)

@login_required
def create_travel_request(request):
    """Create new travel request with enhanced validation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate ER ID - exactly 17 characters
            er_id = data.get('er_id', '').strip()
            if not er_id or len(er_id) != 17:
                return JsonResponse({
                    'success': False,
                    'error': 'ER ID must be exactly 17 characters'
                })
            
            # Validate distance
            distance_km = data.get('distance_km')
            if not distance_km or distance_km < 1:
                return JsonResponse({
                    'success': False,
                    'error': 'Travel distance must be at least 1 KM'
                })
            
            # Validate address - minimum 5 words
            address = data.get('address', '').strip()
            if not address:
                return JsonResponse({
                    'success': False,
                    'error': 'Address is required'
                })
            
            address_words = address.split()
            if len(address_words) < 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Address must contain at least 5 words'
                })
            
            # Validate contact person - exactly 10 digits
            contact_person = data.get('contact_person', '').strip()
            if not contact_person:
                return JsonResponse({
                    'success': False,
                    'error': 'Contact person mobile number is required'
                })
            
            if not contact_person.isdigit() or len(contact_person) != 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Contact person must be exactly 10 digits'
                })
            
            # Validate purpose - minimum 5 words
            purpose = data.get('purpose', '').strip()
            if not purpose:
                return JsonResponse({
                    'success': False,
                    'error': 'Purpose/reason for visit is required'
                })
            
            purpose_words = purpose.split()
            if len(purpose_words) < 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Purpose must contain at least 5 words'
                })
            
            # Remove DCCB restriction - any Associate can approve any travel request
            # No need to find specific Associate based on DCCB
            
            # Create travel request without specific Associate assignment
            travel_request = TravelRequest.objects.create(
                user=request.user,
                from_date=data['from_date'],
                to_date=data['to_date'],
                duration=data['duration'],
                days_count=data['days_count'],
                request_to=None,  # No specific Associate assignment
                er_id=er_id,
                distance_km=distance_km,
                address=address,
                contact_person=contact_person,
                purpose=purpose
            )
            
            # Send notification to all Associates (since any can approve)
            from .notification_service import notify_travel_request
            notify_travel_request(travel_request)
            
            return JsonResponse({
                'success': True,
                'message': 'Travel request submitted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def associate_travel_approvals(request):
    """Travel approval dashboard for Associates - All Associates can approve any travel request"""
    if request.user.designation != 'Associate':
        messages.error(request, 'Access denied. Only Associates can approve travel requests.')
        return redirect('field_dashboard')
    
    # Get filters
    from_date = request.GET.get('from_date', timezone.localdate().isoformat())
    to_date = request.GET.get('to_date', (timezone.localdate() + timedelta(days=30)).isoformat())
    employee_id = request.GET.get('employee_id', '')
    dccb = request.GET.get('dccb', '')
    designation = request.GET.get('designation', '')
    duration = request.GET.get('duration', '')
    status = request.GET.get('status', '')
    
    # Get ALL travel requests from MT/DC/Support users (no DCCB restriction)
    travel_requests = TravelRequest.objects.filter(
        user__designation__in=['MT', 'DC', 'Support'],
        from_date__range=[from_date, to_date]
    ).select_related('user')
    
    # Apply filters
    if employee_id:
        travel_requests = travel_requests.filter(user__employee_id__icontains=employee_id)
    if dccb:
        travel_requests = travel_requests.filter(user__dccb=dccb)
    if designation:
        travel_requests = travel_requests.filter(user__designation=designation)
    if duration:
        travel_requests = travel_requests.filter(duration=duration)
    if status:
        travel_requests = travel_requests.filter(status=status)
    
    # Order by status (pending first)
    travel_requests = travel_requests.order_by(
        Case(
            When(status='pending', then=0),
            When(status='approved', then=1),
            When(status='rejected', then=2),
            default=3
        ),
        '-created_at'
    )
    
    # Pagination
    paginator = Paginator(travel_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id': employee_id,
        'dccb': dccb,
        'designation': designation,
        'duration': duration,
        'status': status,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': [('MT', 'MT'), ('DC', 'DC'), ('Support', 'Support')],
        'duration_choices': TravelRequest.DURATION_CHOICES,
        'status_choices': TravelRequest.STATUS_CHOICES,
    }
    
    return render(request, 'authe/associate_travel_approvals.html', context)

@login_required
def approve_travel_request(request, travel_id):
    """Approve or reject travel request"""
    travel_request = get_object_or_404(TravelRequest, id=travel_id)
    
    # Allow both Associates and Admins to approve travel requests
    if request.user.designation != 'Associate' and request.user.role_level < 10:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    # Associates can approve any travel request (no DCCB restriction)
    # Removed DCCB restriction - any Associate can approve any request
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')  # 'approve' or 'reject'
            remarks = data.get('remarks', '')
            
            if action not in ['approve', 'reject']:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
            
            with transaction.atomic():
                travel_request.status = 'approved' if action == 'approve' else 'rejected'
                travel_request.approved_by = request.user
                travel_request.approved_at = timezone.now()
                travel_request.remarks = remarks
                travel_request.save()
                
                # If approved, update existing attendance records to mark travel as approved
                # Do NOT auto-create attendance - let user mark their own attendance
                if action == 'approve':
                    from .models import Attendance
                    from datetime import timedelta
                    
                    current_date = travel_request.from_date
                    while current_date <= travel_request.to_date:
                        # Only update existing attendance records, don't create new ones
                        existing_attendance = Attendance.objects.filter(
                            user=travel_request.user,
                            date=current_date
                        ).first()
                        
                        if existing_attendance:
                            existing_attendance.travel_approved = True
                            existing_attendance.save()
                        
                        current_date += timedelta(days=1)
                
                # Send notification to user about approval/rejection
                from .notification_service import notify_travel_approval
                notify_travel_approval(travel_request, action == 'approve')
            
            return JsonResponse({
                'success': True,
                'message': f'Travel request {action}d successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def export_travel_requests(request):
    """Export travel request history"""
    travel_requests = TravelRequest.objects.filter(user=request.user).order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="travel_requests_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'From Date', 'To Date', 'Duration', 'Days', 'ER ID', 'Distance (KM)',
        'Address', 'Contact Person', 'Purpose', 'Status', 'Approved By', 'Remarks', 'Created At'
    ])
    
    for tr in travel_requests:
        writer.writerow([
            tr.from_date,
            tr.to_date,
            tr.get_duration_display(),
            tr.days_count,
            tr.er_id,
            tr.distance_km,
            tr.address,
            tr.contact_person,
            tr.purpose,
            tr.get_status_display(),
            tr.approved_by.employee_id if tr.approved_by else '',
            tr.remarks or '',
            tr.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response