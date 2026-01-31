from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import TravelRequest

@login_required
def travel_request_details_api(request, travel_id):
    """API to get travel request details for Associates and Admins"""
    if request.user.designation not in ['Associate'] and request.user.role_level < 10:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        travel_request = get_object_or_404(TravelRequest, id=travel_id)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(travel_request.id),
                'employee_id': travel_request.user.employee_id,
                'employee_name': f"{travel_request.user.first_name} {travel_request.user.last_name}",
                'dccb': travel_request.user.dccb or 'N/A',
                'designation': travel_request.user.designation,
                'from_date': travel_request.from_date.strftime('%d %b %Y'),
                'to_date': travel_request.to_date.strftime('%d %b %Y'),
                'duration': travel_request.get_duration_display(),
                'days_count': str(travel_request.days_count),
                'er_id': travel_request.er_id,
                'distance_km': travel_request.distance_km,
                'address': travel_request.address,
                'contact_person': travel_request.contact_person,
                'purpose': travel_request.purpose,
                'status': travel_request.status,
                'created_at': travel_request.created_at.strftime('%d %b %Y %H:%M'),
                'remarks': travel_request.remarks or 'No remarks'
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})