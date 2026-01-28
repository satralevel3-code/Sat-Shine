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

def test_updated_associate_dashboard():
    print("=" * 80)
    print("TESTING UPDATED ASSOCIATE DASHBOARD")
    print("=" * 80)
    
    # Get an Associate user
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    test_associate = associates.first()
    print(f"Testing with Associate: {test_associate.employee_id}")
    
    # Test the NEW date range logic (from associate_views.py)
    from_date = (timezone.localdate() - timedelta(days=30)).isoformat()
    to_date = (timezone.localdate() + timedelta(days=60)).isoformat()
    
    print(f"\nNEW Default date range:")
    print(f"  From: {from_date}")
    print(f"  To: {to_date}")
    
    # Test the travel request query with new date range
    travel_requests = TravelRequest.objects.filter(
        user__designation__in=['MT', 'DC', 'Support'],
        from_date__range=[from_date, to_date]
    ).select_related('user')
    
    print(f"\nTravel requests found with NEW range: {travel_requests.count()}")
    
    if travel_requests.exists():
        print("Travel requests that will show:")
        for tr in travel_requests:
            print(f"  - {tr.user.employee_id} ({tr.user.designation}): {tr.from_date} to {tr.to_date} - {tr.status}")
    else:
        print("Still no travel requests found!")
    
    print("\n" + "=" * 80)
    print("RESULT: Associates should now see ALL travel requests")
    print("=" * 80)

if __name__ == "__main__":
    test_updated_associate_dashboard()