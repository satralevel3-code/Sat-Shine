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

def diagnose_production():
    print("=" * 80)
    print("PRODUCTION DATABASE DIAGNOSTIC")
    print("=" * 80)
    
    # Check database type
    from django.conf import settings
    db_engine = settings.DATABASES['default']['ENGINE']
    print(f"Database: {db_engine}")
    
    # Check all users
    all_users = CustomUser.objects.all()
    print(f"\nTotal Users: {all_users.count()}")
    
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    print(f"Associates: {associates.count()}")
    for assoc in associates:
        print(f"  - {assoc.employee_id}: {assoc.first_name} {assoc.last_name}")
    
    field_officers = CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'], is_active=True)
    print(f"\nField Officers (MT/DC/Support): {field_officers.count()}")
    for officer in field_officers:
        print(f"  - {officer.employee_id}: {officer.designation}")
    
    # Check travel requests
    all_travel_requests = TravelRequest.objects.all()
    print(f"\nTotal Travel Requests: {all_travel_requests.count()}")
    
    if all_travel_requests.exists():
        print("Travel Requests:")
        for tr in all_travel_requests:
            print(f"  - ID: {tr.id}, User: {tr.user.employee_id} ({tr.user.designation})")
            print(f"    Dates: {tr.from_date} to {tr.to_date}, Status: {tr.status}")
    else:
        print("NO TRAVEL REQUESTS FOUND IN PRODUCTION!")
    
    # Test Associate query with production data
    if associates.exists():
        test_associate = associates.first()
        print(f"\nTesting Associate Query: {test_associate.employee_id}")
        
        # Use the updated date range
        from_date = (timezone.localdate() - timedelta(days=30)).isoformat()
        to_date = (timezone.localdate() + timedelta(days=60)).isoformat()
        
        travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
        
        print(f"Date range: {from_date} to {to_date}")
        print(f"Query result: {travel_requests.count()} requests")
        
        if travel_requests.exists():
            for tr in travel_requests:
                print(f"  - {tr.user.employee_id}: {tr.from_date} to {tr.to_date}")
        else:
            print("  No requests found in date range")
    
    print("\n" + "=" * 80)
    print("PRODUCTION STATUS")
    print("=" * 80)

if __name__ == "__main__":
    diagnose_production()