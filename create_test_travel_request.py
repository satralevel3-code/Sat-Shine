#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.utils import timezone
from datetime import date

def create_test_travel_requests():
    print("=" * 80)
    print("CREATING TEST TRAVEL REQUESTS FOR PRODUCTION")
    print("=" * 80)
    
    # Get field officers
    field_officers = CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'], is_active=True)
    
    if not field_officers.exists():
        print("No field officers found! Creating test users first...")
        return
    
    # Create test travel requests
    test_officer = field_officers.first()
    print(f"Creating travel request for: {test_officer.employee_id}")
    
    # Create a travel request for today
    travel_request = TravelRequest.objects.create(
        user=test_officer,
        from_date=date.today(),
        to_date=date.today(),
        duration='full_day',
        days_count=1,
        er_id='ER12345678901234567',
        distance_km=50,
        address='Test Address for Production Travel Request Testing Purpose',
        contact_person='9876543210',
        purpose='Production testing travel request for Associate dashboard verification system',
        status='pending'
    )
    
    print(f"Created travel request ID: {travel_request.id}")
    
    # Verify it was created
    all_requests = TravelRequest.objects.all()
    print(f"Total travel requests now: {all_requests.count()}")
    
    # Test Associate query
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    if associates.exists():
        test_associate = associates.first()
        print(f"\nTesting with Associate: {test_associate.employee_id}")
        
        from datetime import timedelta
        from_date = (timezone.localdate() - timedelta(days=30)).isoformat()
        to_date = (timezone.localdate() + timedelta(days=60)).isoformat()
        
        travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
        
        print(f"Associate will see: {travel_requests.count()} travel requests")
        
        if travel_requests.exists():
            for tr in travel_requests:
                print(f"  - {tr.user.employee_id}: {tr.from_date} ({tr.status})")
    
    print("\n" + "=" * 80)
    print("TEST TRAVEL REQUEST CREATED - Check Associate dashboard now")
    print("=" * 80)

if __name__ == "__main__":
    create_test_travel_requests()