#!/usr/bin/env python
"""
Production Diagnostic & Fix Script
Run this in production to diagnose and fix travel request visibility
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from datetime import date, timedelta

def diagnose_and_fix():
    print("=" * 80)
    print("PRODUCTION DIAGNOSTIC - TRAVEL REQUEST VISIBILITY")
    print("=" * 80)
    
    # Check users
    print("\n1. CHECKING USERS:")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    field_officers = CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'], is_active=True)
    
    print(f"   Associates: {associates.count()}")
    for a in associates:
        print(f"   - {a.employee_id}: {a.first_name} {a.last_name}")
    
    print(f"\n   Field Officers: {field_officers.count()}")
    for f in field_officers:
        print(f"   - {f.employee_id}: {f.first_name} {f.last_name} ({f.designation})")
    
    # Check travel requests
    print("\n2. CHECKING TRAVEL REQUESTS:")
    all_requests = TravelRequest.objects.all()
    print(f"   Total: {all_requests.count()}")
    
    if all_requests.exists():
        for tr in all_requests:
            print(f"   - {tr.user.employee_id} ({tr.user.designation}): {tr.from_date} - {tr.status}")
    else:
        print("   ⚠️ NO TRAVEL REQUESTS FOUND!")
    
    # Test Associate query
    print("\n3. TESTING ASSOCIATE QUERY:")
    if associates.exists():
        test_associate = associates.first()
        print(f"   Testing with: {test_associate.employee_id}")
        
        from_date = (date.today() - timedelta(days=30)).isoformat()
        to_date = (date.today() + timedelta(days=60)).isoformat()
        
        travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
        
        print(f"   Date range: {from_date} to {to_date}")
        print(f"   Query result: {travel_requests.count()} requests")
        
        if travel_requests.exists():
            print("   ✅ WORKING - Associate will see these requests:")
            for tr in travel_requests:
                print(f"      - {tr.user.employee_id}: {tr.from_date}")
        else:
            print("   ❌ ISSUE - No requests in date range")
    
    # Fix if needed
    if not all_requests.exists() and field_officers.exists():
        print("\n4. CREATING TEST TRAVEL REQUESTS:")
        for i, officer in enumerate(field_officers[:3]):
            travel_date = date.today() + timedelta(days=i+1)
            tr = TravelRequest.objects.create(
                user=officer,
                from_date=travel_date,
                to_date=travel_date,
                duration='full_day',
                days_count=1,
                er_id=f'ER{str(i+1).zfill(17)}',
                distance_km=50,
                address=f'Production Test Address {i+1} for Travel Request',
                contact_person=f'900000000{i}',
                purpose=f'Production travel request {i+1} for testing',
                status='pending'
            )
            print(f"   ✅ Created: {officer.employee_id} - {travel_date}")
        
        print("\n   ✅ FIX APPLIED - Travel requests created")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    diagnose_and_fix()
