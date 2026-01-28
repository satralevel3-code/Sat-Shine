#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest, Attendance, LeaveRequest
from django.utils import timezone
from datetime import timedelta

def test_associate_dashboard_view():
    print("=" * 80)
    print("TESTING ASSOCIATE DASHBOARD VIEW")
    print("=" * 80)
    
    # Get an Associate user
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    if not associates.exists():
        print("ERROR: No Associate users found!")
        return
    
    test_associate = associates.first()
    print(f"Testing with Associate: {test_associate.employee_id} - {test_associate.first_name} {test_associate.last_name}")
    
    print("\n1. SIMULATING ASSOCIATE DASHBOARD VIEW:")
    print("-" * 40)
    
    # Get today's attendance
    today = timezone.localdate()
    today_attendance = Attendance.objects.filter(user=test_associate, date=today).first()
    print(f"Today's attendance: {today_attendance}")
    
    # Get recent attendance
    week_ago = today - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(
        user=test_associate, 
        date__gte=week_ago
    ).order_by('-date')[:7]
    print(f"Recent attendance count: {recent_attendance.count()}")
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.objects.filter(
        user=test_associate, 
        status='pending'
    ).count()
    print(f"Pending leaves: {pending_leaves}")
    
    # Get travel request filters (default values)
    from_date = timezone.localdate().isoformat()
    to_date = (timezone.localdate() + timedelta(days=30)).isoformat()
    
    print(f"Date range: {from_date} to {to_date}")
    
    # Test the travel request query
    print("\n2. TESTING TRAVEL REQUEST QUERY:")
    print("-" * 40)
    
    # This is the exact query from associate_dashboard
    travel_requests = TravelRequest.objects.filter(
        user__designation__in=['MT', 'DC', 'Support'],
        from_date__range=[from_date, to_date]
    ).select_related('user')
    
    print(f"Travel requests found: {travel_requests.count()}")
    
    if travel_requests.exists():
        print("Travel requests details:")
        for tr in travel_requests:
            print(f"  - ID: {tr.id}, User: {tr.user.employee_id} ({tr.user.designation})")
            print(f"    Dates: {tr.from_date} to {tr.to_date}")
            print(f"    Status: {tr.status}")
    else:
        print("No travel requests found!")
        
        # Debug: Check all travel requests
        all_requests = TravelRequest.objects.all()
        print(f"\nTotal travel requests in DB: {all_requests.count()}")
        
        if all_requests.exists():
            print("All travel requests:")
            for tr in all_requests:
                print(f"  - ID: {tr.id}, User: {tr.user.employee_id} ({tr.user.designation})")
                print(f"    Dates: {tr.from_date} to {tr.to_date}")
                print(f"    In date range? {from_date <= tr.from_date.isoformat() <= to_date}")
    
    # Test context creation
    print("\n3. TESTING CONTEXT CREATION:")
    print("-" * 40)
    
    context = {
        'user': test_associate,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'travel_requests': travel_requests,
        'from_date': from_date,
        'to_date': to_date,
        'current_time': timezone.now(),
    }
    
    print(f"Context travel_requests count: {context['travel_requests'].count()}")
    print(f"Context keys: {list(context.keys())}")
    
    # Test template rendering simulation
    print("\n4. TEMPLATE RENDERING SIMULATION:")
    print("-" * 40)
    
    print("Template will render:")
    if context['travel_requests'].exists():
        print(f"  - {context['travel_requests'].count()} travel request rows")
        for tr in context['travel_requests']:
            print(f"    * {tr.user.employee_id} - {tr.from_date} to {tr.to_date} ({tr.status})")
    else:
        print("  - 'No travel requests found' message")
    
    print("\n5. URL AND ROUTING CHECK:")
    print("-" * 40)
    
    # Check URL routing
    from django.urls import reverse
    try:
        url = reverse('associate_dashboard')
        print(f"Associate dashboard URL: {url}")
    except Exception as e:
        print(f"URL routing error: {e}")
    
    # Check travel request details URL
    try:
        if travel_requests.exists():
            test_id = travel_requests.first().id
            details_url = reverse('travel_request_details', args=[test_id])
            print(f"Travel request details URL: {details_url}")
    except Exception as e:
        print(f"Travel details URL error: {e}")
    
    # Test actual view call
    print("\n6. ACTUAL VIEW CALL TEST:")
    print("-" * 40)
    
    try:
        from django.test import RequestFactory
        from authe.associate_views import associate_dashboard
        
        factory = RequestFactory()
        request = factory.get('/auth/associate-dashboard/')
        request.user = test_associate
        
        # Call the actual view
        response = associate_dashboard(request)
        print(f"View response status: {response.status_code}")
        
        if hasattr(response, 'context_data'):
            print(f"Response context keys: {list(response.context_data.keys())}")
        
    except Exception as e:
        print(f"View call error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_associate_dashboard_view()