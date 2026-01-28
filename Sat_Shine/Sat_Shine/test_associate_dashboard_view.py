#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.utils import timezone
from datetime import timedelta
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from authe.associate_views import associate_dashboard

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
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/auth/associate-dashboard/')
    request.user = test_associate
    
    # Test the view function directly
    try:
        print("\n1. CALLING associate_dashboard VIEW:")
        print("-" * 40)
        
        # Import and call the view
        from authe.associate_views import associate_dashboard
        
        # Simulate the view logic manually
        from django.utils import timezone
        from datetime import timedelta
        from authe.models import Attendance, LeaveRequest, TravelRequest
        
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
        
        print(f"Travel requests found: {travel_requests.count()}")\n        \n        if travel_requests.exists():\n            print(\"Travel requests details:\")\n            for tr in travel_requests:\n                print(f\"  - ID: {tr.id}, User: {tr.user.employee_id} ({tr.user.designation})\")\n                print(f\"    Dates: {tr.from_date} to {tr.to_date}\")\n                print(f\"    Status: {tr.status}\")\n        else:\n            print(\"No travel requests found!\")\n            \n            # Debug: Check all travel requests\n            all_requests = TravelRequest.objects.all()\n            print(f\"\\nTotal travel requests in DB: {all_requests.count()}\")\n            \n            if all_requests.exists():\n                print(\"All travel requests:\")\n                for tr in all_requests:\n                    print(f\"  - ID: {tr.id}, User: {tr.user.employee_id} ({tr.user.designation})\")\n                    print(f\"    Dates: {tr.from_date} to {tr.to_date}\")\n                    print(f\"    In date range? {from_date <= tr.from_date.isoformat() <= to_date}\")\n        \n        # Test context creation\n        print(\"\\n3. TESTING CONTEXT CREATION:\")\n        print(\"-\" * 40)\n        \n        context = {\n            'user': test_associate,\n            'today_attendance': today_attendance,\n            'recent_attendance': recent_attendance,\n            'pending_leaves': pending_leaves,\n            'travel_requests': travel_requests,\n            'from_date': from_date,\n            'to_date': to_date,\n            'current_time': timezone.now(),\n        }\n        \n        print(f\"Context travel_requests count: {context['travel_requests'].count()}\")\n        print(f\"Context keys: {list(context.keys())}\")\n        \n        # Test template rendering simulation\n        print(\"\\n4. TEMPLATE RENDERING SIMULATION:\")\n        print(\"-\" * 40)\n        \n        print(\"Template will render:\")\n        if context['travel_requests'].exists():\n            print(f\"  - {context['travel_requests'].count()} travel request rows\")\n            for tr in context['travel_requests']:\n                print(f\"    * {tr.user.employee_id} - {tr.from_date} to {tr.to_date} ({tr.status})\")\n        else:\n            print(\"  - 'No travel requests found' message\")\n        \n        print(\"\\n5. URL AND ROUTING CHECK:\")\n        print(\"-\" * 40)\n        \n        # Check URL routing\n        from django.urls import reverse\n        try:\n            url = reverse('associate_dashboard')\n            print(f\"Associate dashboard URL: {url}\")\n        except Exception as e:\n            print(f\"URL routing error: {e}\")\n        \n        # Check travel request details URL\n        try:\n            if travel_requests.exists():\n                test_id = travel_requests.first().id\n                details_url = reverse('travel_request_details', args=[test_id])\n                print(f\"Travel request details URL: {details_url}\")\n        except Exception as e:\n            print(f\"Travel details URL error: {e}\")\n            \n    except Exception as e:\n        print(f\"ERROR in view testing: {e}\")\n        import traceback\n        traceback.print_exc()\n    \n    print(\"\\n\" + \"=\" * 80)\n    print(\"TEST COMPLETE\")\n    print(\"=\" * 80)\n\nif __name__ == \"__main__\":\n    test_associate_dashboard_view()