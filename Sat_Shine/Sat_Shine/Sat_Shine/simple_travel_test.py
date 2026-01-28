#!/usr/bin/env python
"""
Simple Local Travel Request Test
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.db import transaction
from django.utils import timezone

def simple_test():
    print("=== SIMPLE TRAVEL REQUEST TEST ===\n")
    
    # 1. Setup Users
    print("1. Setting up users...")
    
    with transaction.atomic():
        # Associate
        associate, created = CustomUser.objects.get_or_create(
            employee_id='MP0001',
            defaults={
                'email': 'associate@test.com',
                'first_name': 'TEST',
                'last_name': 'ASSOCIATE',
                'designation': 'Associate',
                'role': 'admin',
                'contact_number': '9999999999',
                'multiple_dccb': ['AHMEDABAD', 'BARODA', 'BHARUCH'],
                'can_approve_travel': True,
                'role_level': 7
            }
        )
        
        if not created:
            associate.multiple_dccb = ['AHMEDABAD', 'BARODA', 'BHARUCH']
            associate.can_approve_travel = True
            associate.role_level = 7
            associate.save()
        
        # Field User
        field_user, created = CustomUser.objects.get_or_create(
            employee_id='MGJ00001',
            defaults={
                'email': 'field@test.com',
                'first_name': 'TEST',
                'last_name': 'FIELD',
                'designation': 'MT',
                'role': 'field_officer',
                'contact_number': '8888888888',
                'dccb': 'AHMEDABAD'
            }
        )
        
        if not created:
            field_user.dccb = 'AHMEDABAD'
            field_user.designation = 'MT'
            field_user.save()
    
    print(f"   Associate: {associate.employee_id}")
    print(f"   Field User: {field_user.employee_id}")
    
    # 2. Create Travel Request
    print("\n2. Creating travel request...")
    
    TravelRequest.objects.filter(er_id__startswith='TEST').delete()
    
    test_request = TravelRequest.objects.create(
        user=field_user,
        from_date=timezone.localdate(),
        to_date=timezone.localdate() + timedelta(days=1),
        duration='full_day',
        days_count=1.0,
        request_to=associate,
        er_id='TEST12345678901234567',
        distance_km=50,
        address='Test Address for Local Testing Purpose Only',
        contact_person='9876543210',
        purpose='Test travel request for local system verification and testing'
    )
    
    print(f"   Request ID: {test_request.id}")
    print(f"   Status: {test_request.status}")
    
    # 3. Test Associate Dashboard Query
    print("\n3. Testing Associate dashboard query...")
    
    # This is the query from associate_dashboard view
    user_dccbs = associate.multiple_dccb or []
    print(f"   Associate DCCBs: {user_dccbs}")
    
    # Query 1: Original (only assigned requests)
    assigned_requests = TravelRequest.objects.filter(request_to=associate)
    print(f"   Assigned requests: {assigned_requests.count()}")
    
    # Query 2: New (DCCB-based)
    dccb_requests = TravelRequest.objects.filter(user__dccb__in=user_dccbs)
    print(f"   DCCB-based requests: {dccb_requests.count()}")
    
    # Query 3: Combined (both assigned and DCCB-based)
    from django.db.models import Q
    combined_requests = TravelRequest.objects.filter(
        Q(user__dccb__in=user_dccbs) | Q(request_to=associate)
    )
    print(f"   Combined requests: {combined_requests.count()}")
    
    # 4. Test Approval Logic
    print("\n4. Testing approval logic...")
    
    # Check if Associate can approve this request
    requester_dccb = test_request.user.dccb
    print(f"   Requester DCCB: {requester_dccb}")
    print(f"   Associate DCCBs: {user_dccbs}")
    print(f"   Can approve: {requester_dccb in user_dccbs}")
    
    # 5. Test Approval Function Logic
    print("\n5. Testing approval function...")
    
    # Simulate the approval logic from approve_travel_request view
    if associate.designation == 'Associate':
        user_dccbs = associate.multiple_dccb or []
        requester_dccb = test_request.user.dccb
        
        if requester_dccb not in user_dccbs:
            print(f"   ERROR: Cannot approve - DCCB mismatch")
            print(f"   Required: {requester_dccb}")
            print(f"   Available: {user_dccbs}")
        else:
            print(f"   OK: Can approve request")
            
            # Simulate approval
            test_request.status = 'approved'
            test_request.approved_by = associate
            test_request.approved_at = timezone.now()
            test_request.remarks = 'Test approval'
            test_request.save()
            
            print(f"   Approved successfully")
            print(f"   New status: {test_request.status}")
            print(f"   Approved by: {test_request.approved_by.employee_id}")
    
    # 6. Final Verification
    print("\n6. Final verification...")
    
    # Check all travel requests visible to Associate
    visible_requests = TravelRequest.objects.filter(
        Q(user__dccb__in=associate.multiple_dccb) | Q(request_to=associate)
    )
    
    print(f"   Total visible requests: {visible_requests.count()}")
    for req in visible_requests:
        print(f"     - ID: {req.id}, User: {req.user.employee_id} ({req.user.dccb}), Status: {req.status}")
    
    print("\n=== TEST RESULTS ===")
    print(f"Associate User: {associate.employee_id}")
    print(f"  - DCCBs: {associate.multiple_dccb}")
    print(f"  - Can approve travel: {associate.can_approve_travel}")
    print(f"  - Role level: {associate.role_level}")
    
    print(f"\nField User: {field_user.employee_id}")
    print(f"  - DCCB: {field_user.dccb}")
    print(f"  - Designation: {field_user.designation}")
    
    print(f"\nTravel Request: {test_request.id}")
    print(f"  - Status: {test_request.status}")
    print(f"  - Assigned to: {test_request.request_to.employee_id if test_request.request_to else 'None'}")
    print(f"  - Approved by: {test_request.approved_by.employee_id if test_request.approved_by else 'None'}")
    
    print("\nNext steps:")
    print("1. Start server: python manage.py runserver")
    print("2. Login as Associate: MP0001")
    print("3. Check associate dashboard")

if __name__ == '__main__':
    simple_test()