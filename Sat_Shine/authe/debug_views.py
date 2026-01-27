from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import CustomUser, TravelRequest, Attendance
from datetime import timedelta

@login_required
def debug_travel_requests(request):
    """Debug view to check travel requests in database"""
    if not request.user.role_level >= 10:
        return JsonResponse({'error': 'Access denied'})
    
    # Count all travel requests
    total_travel_requests = TravelRequest.objects.count()
    
    # Get recent travel requests
    recent_requests = TravelRequest.objects.all().order_by('-created_at')[:10]
    
    # Count by status
    pending_count = TravelRequest.objects.filter(status='pending').count()
    approved_count = TravelRequest.objects.filter(status='approved').count()
    rejected_count = TravelRequest.objects.filter(status='rejected').count()
    
    # Get users who can create travel requests
    mt_dc_support_users = CustomUser.objects.filter(
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    ).count()
    
    # Get Associates who can approve
    associates = CustomUser.objects.filter(
        designation='Associate',
        is_active=True
    ).count()
    
    debug_info = {
        'total_travel_requests': total_travel_requests,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'mt_dc_support_users': mt_dc_support_users,
        'associates_count': associates,
        'recent_requests': [
            {
                'id': req.id,
                'user': req.user.employee_id,
                'from_date': req.from_date.isoformat(),
                'to_date': req.to_date.isoformat(),
                'status': req.status,
                'created_at': req.created_at.isoformat(),
                'request_to': req.request_to.employee_id if req.request_to else None
            }
            for req in recent_requests
        ]
    }
    
    return JsonResponse(debug_info, indent=2)

@login_required
def create_sample_travel_request(request):
    """Create a sample travel request for testing"""
    if not request.user.role_level >= 10:
        return JsonResponse({'error': 'Access denied'})
    
    # Find an MT/DC/Support user
    field_user = CustomUser.objects.filter(
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    ).first()
    
    if not field_user:
        return JsonResponse({'error': 'No MT/DC/Support users found'})
    
    # Find an Associate for the same DCCB
    associate = None
    if field_user.dccb:
        associates = CustomUser.objects.filter(
            designation='Associate',
            is_active=True
        )
        
        for assoc in associates:
            if assoc.multiple_dccb and field_user.dccb in assoc.multiple_dccb:
                associate = assoc
                break
    
    if not associate:
        # Just use any Associate
        associate = CustomUser.objects.filter(
            designation='Associate',
            is_active=True
        ).first()
    
    if not associate:
        return JsonResponse({'error': 'No Associates found'})
    
    # Create sample travel request
    today = timezone.localdate()
    travel_request = TravelRequest.objects.create(
        user=field_user,
        from_date=today + timedelta(days=1),
        to_date=today + timedelta(days=1),
        duration='full_day',
        days_count=1.0,
        request_to=associate,
        er_id='SAMPLE12345678901',  # 17 characters
        distance_km=50,
        address='Sample Address Line 1, Sample City, Sample State, Sample Country, PIN 123456',
        contact_person='9876543210',
        purpose='Sample business visit for client meeting and documentation review process'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Sample travel request created',
        'travel_request': {
            'id': travel_request.id,
            'user': travel_request.user.employee_id,
            'request_to': travel_request.request_to.employee_id,
            'from_date': travel_request.from_date.isoformat(),
            'status': travel_request.status
        }
    })