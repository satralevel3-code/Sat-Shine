# Enterprise Travel Request Views for MMP

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime
from .models import TravelRequest, CustomUser
from .enterprise_permissions import check_hierarchy_permission, log_enterprise_action
import json

@login_required
@csrf_exempt
@require_http_methods(["POST", "GET"])
def request_travel(request):
    """Create travel request - Field Officers"""
    if request.user.role not in ['field_officer', 'dc', 'mt', 'support']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = request.POST if request.content_type != 'application/json' else json.loads(request.body)
            
            travel_request = TravelRequest.objects.create(
                user=request.user,
                from_date=datetime.strptime(data.get('from_date'), '%Y-%m-%d').date(),
                to_date=datetime.strptime(data.get('to_date'), '%Y-%m-%d').date(),
                er_id=data.get('er_id'),
                distance_km=int(data.get('distance_km')),
                address=data.get('address'),
                contact_person=data.get('contact_person'),
                purpose=data.get('purpose')
            )
            
            # Enterprise audit logging
            log_enterprise_action(
                user=request.user,
                action_type='TRAVEL_REQUEST_CREATED',
                target_table='travel_requests',
                target_id=travel_request.id,
                new_value={
                    'from_date': str(travel_request.from_date),
                    'to_date': str(travel_request.to_date),
                    'purpose': travel_request.purpose
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Travel request submitted successfully')
            return redirect('field_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting travel request: {str(e)}')
            return redirect('request_travel')
    
    # GET request
    recent_requests = TravelRequest.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'travel_requests': recent_requests,
    }
    return render(request, 'authe/request_travel.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def approve_travel(request, travel_id):
    """Approve/Reject travel request - Associates"""
    if not request.user.can_approve_travel:
        return JsonResponse({'error': 'Travel approval permission required'}, status=403)
    
    try:
        travel_request = TravelRequest.objects.get(id=travel_id, status='pending')
        
        # Check hierarchy permission
        if not check_hierarchy_permission(request.user, travel_request.user, 'approve_travel'):
            return JsonResponse({'error': 'Insufficient permissions'}, status=403)
        
        data = json.loads(request.body)
        decision = data.get('decision')  # 'approved' or 'rejected'
        remarks = data.get('remarks', '')
        
        old_status = travel_request.status
        travel_request.status = decision
        travel_request.approved_by = request.user
        travel_request.approved_at = timezone.now()
        travel_request.remarks = remarks
        travel_request.save()
        
        # Enterprise audit logging
        log_enterprise_action(
            user=request.user,
            action_type='TRAVEL_REQUEST_APPROVED',
            target_table='travel_requests',
            target_id=travel_request.id,
            old_value={'status': old_status},
            new_value={'status': decision, 'remarks': remarks},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Travel request {decision}'
        })
        
    except TravelRequest.DoesNotExist:
        return JsonResponse({'error': 'Travel request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def travel_approvals(request):
    """Travel approval dashboard - Associates"""
    if not request.user.can_approve_travel:
        messages.error(request, 'Travel approval permission required')
        return redirect('field_dashboard')
    
    # Get pending travel requests for approval
    pending_requests = TravelRequest.objects.filter(
        status='pending',
        user__dccb=request.user.dccb  # Same DCCB only
    ).order_by('-created_at')
    
    context = {
        'user': request.user,
        'pending_requests': pending_requests,
    }
    return render(request, 'authe/travel_approvals.html', context)