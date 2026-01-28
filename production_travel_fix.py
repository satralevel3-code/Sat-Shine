#!/usr/bin/env python
"""
Production Travel Request Diagnostic & Fix Script
Comprehensive analysis and resolution for Associate approval issues
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.db import transaction
from django.utils import timezone

def diagnose_and_fix():
    print("=== PRODUCTION TRAVEL REQUEST DIAGNOSTIC ===\n")
    
    issues_found = []
    fixes_applied = []
    
    # 1. Check Associate users
    print("1. Checking Associate users...")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    
    if not associates.exists():
        print("   ✗ CRITICAL: No Associate users found!")
        issues_found.append("No Associate users")
        
        # Create Associate user
        with transaction.atomic():
            associate = CustomUser.objects.create_user(
                employee_id='MP0001',
                email='associate@satshine.com',
                password='Associate123!',
                first_name='SYSTEM',
                last_name='ASSOCIATE',
                designation='Associate',
                role='admin',
                contact_number='9999999999',
                multiple_dccb=['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA', 'MAHESANA', 'BANASKANTHA'],
                can_approve_travel=True,
                role_level=7
            )
            fixes_applied.append(f"Created Associate user: {associate.employee_id}")
            print(f"   ✓ FIXED: Created Associate user {associate.employee_id}")
    else:
        for assoc in associates:
            print(f"   ✓ Found Associate: {assoc.employee_id}")
            
            # Check and fix multiple_dccb
            if not assoc.multiple_dccb or len(assoc.multiple_dccb) == 0:
                assoc.multiple_dccb = ['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA']
                assoc.save()
                fixes_applied.append(f"Fixed DCCBs for {assoc.employee_id}")
                print(f"   ✓ FIXED: Added DCCBs to {assoc.employee_id}")
            
            # Check travel approval permission
            if not assoc.can_approve_travel:
                assoc.can_approve_travel = True
                assoc.save()
                fixes_applied.append(f"Enabled travel approval for {assoc.employee_id}")
                print(f"   ✓ FIXED: Enabled travel approval for {assoc.employee_id}")
    
    # 2. Check user MGJ00002
    print(f"\n2. Checking user MGJ00002...")
    try:
        user = CustomUser.objects.get(employee_id='MGJ00002')
        print(f"   ✓ User found: {user.first_name} {user.last_name}")
        print(f"   DCCB: {user.dccb}")
        print(f"   Designation: {user.designation}")
        
        # Fix DCCB if missing
        if not user.dccb:
            user.dccb = 'AHMEDABAD'
            user.save()
            fixes_applied.append("Assigned DCCB to MGJ00002")
            print(f"   ✓ FIXED: Assigned DCCB 'AHMEDABAD' to MGJ00002")
        
        # Fix designation if invalid
        if user.designation not in ['MT', 'DC', 'Support']:
            user.designation = 'MT'
            user.save()
            fixes_applied.append("Fixed designation for MGJ00002")
            print(f"   ✓ FIXED: Set designation to 'MT' for MGJ00002")
            
    except CustomUser.DoesNotExist:
        print("   ✗ CRITICAL: User MGJ00002 not found!")
        issues_found.append("MGJ00002 user missing")
    
    # 3. Check travel requests
    print(f"\n3. Checking travel requests...")
    
    # Get all travel requests
    all_requests = TravelRequest.objects.all().order_by('-created_at')
    print(f"   Total travel requests: {all_requests.count()}")
    
    # Check for orphaned requests (no request_to)
    orphaned = TravelRequest.objects.filter(request_to__isnull=True)
    if orphaned.exists():
        print(f"   ✗ Found {orphaned.count()} orphaned travel requests")
        issues_found.append(f"{orphaned.count()} orphaned requests")
        
        # Fix orphaned requests
        associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
        if associate:
            count = orphaned.update(request_to=associate)
            fixes_applied.append(f"Fixed {count} orphaned requests")
            print(f"   ✓ FIXED: Assigned {count} orphaned requests to {associate.employee_id}")
    
    # Check requests for MGJ00002
    mgj_requests = TravelRequest.objects.filter(user__employee_id='MGJ00002')
    print(f"   MGJ00002 travel requests: {mgj_requests.count()}")
    
    for req in mgj_requests[:3]:  # Show last 3
        print(f"     - ID: {req.id}, Status: {req.status}, To: {req.request_to.employee_id if req.request_to else 'None'}")
    
    # 4. Check URL routing
    print(f"\n4. Checking URL routing...")
    try:
        from django.urls import reverse
        
        # Test critical URLs
        test_urls = [
            ('associate_dashboard', []),
            ('travel_request_details', [1]),
            ('approve_travel_request', [1]),
            ('associate_travel_approvals', [])
        ]
        
        for url_name, args in test_urls:
            try:
                url = reverse(url_name, args=args)
                print(f"   ✓ {url_name}: {url}")
            except Exception as e:
                print(f"   ✗ {url_name}: {e}")
                issues_found.append(f"URL routing issue: {url_name}")
                
    except Exception as e:
        print(f"   ✗ URL check failed: {e}")
        issues_found.append("URL routing problems")
    
    # 5. Check database constraints
    print(f"\n5. Checking database integrity...")
    
    # Check for missing foreign key relationships
    invalid_requests = TravelRequest.objects.filter(
        request_to__isnull=False
    ).exclude(
        request_to__in=CustomUser.objects.filter(designation='Associate')
    )
    
    if invalid_requests.exists():
        print(f"   ✗ Found {invalid_requests.count()} requests with invalid Associates")
        issues_found.append("Invalid Associate assignments")
        
        # Fix invalid assignments
        valid_associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
        if valid_associate:
            count = invalid_requests.update(request_to=valid_associate)
            fixes_applied.append(f"Fixed {count} invalid Associate assignments")
            print(f"   ✓ FIXED: Reassigned {count} requests to valid Associate")
    
    # 6. Test Associate login capability
    print(f"\n6. Testing Associate authentication...")
    try:
        associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
        if associate:
            # Test password
            if associate.check_password('Associate123!'):
                print(f"   ✓ Associate {associate.employee_id} password is correct")
            else:
                associate.set_password('Associate123!')
                associate.save()
                fixes_applied.append(f"Reset password for {associate.employee_id}")
                print(f"   ✓ FIXED: Reset password for {associate.employee_id}")
        else:
            print("   ✗ No Associate user available for testing")
            issues_found.append("No Associate for authentication test")
            
    except Exception as e:
        print(f"   ✗ Authentication test failed: {e}")
        issues_found.append("Authentication issues")
    
    # 7. Create test travel request if none exist
    print(f"\n7. Creating test data if needed...")
    
    try:
        mgj_user = CustomUser.objects.get(employee_id='MGJ00002')
        associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
        
        if associate and mgj_requests.count() == 0:
            # Create a test travel request
            test_request = TravelRequest.objects.create(
                user=mgj_user,
                from_date=timezone.localdate(),
                to_date=timezone.localdate() + timedelta(days=1),
                duration='full_day',
                days_count=1.0,
                request_to=associate,
                er_id='TEST12345678901234567',
                distance_km=50,
                address='Test Address for Travel Request Verification Purpose Only',
                contact_person='9876543210',
                purpose='Test travel request created for system verification and debugging purposes only'
            )
            fixes_applied.append(f"Created test travel request ID: {test_request.id}")
            print(f"   ✓ Created test travel request ID: {test_request.id}")
            
    except Exception as e:
        print(f"   ✗ Test data creation failed: {e}")
    
    # 8. Final verification
    print(f"\n8. Final system verification...")
    
    # Verify Associate can see travel requests
    associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
    if associate:
        # Check if Associate has DCCBs that match user requests
        user_dccbs = set()
        for req in TravelRequest.objects.all():
            if req.user.dccb:
                user_dccbs.add(req.user.dccb)
        
        associate_dccbs = set(associate.multiple_dccb or [])
        matching_dccbs = user_dccbs.intersection(associate_dccbs)
        
        print(f"   User DCCBs in requests: {user_dccbs}")
        print(f"   Associate DCCBs: {associate_dccbs}")
        print(f"   Matching DCCBs: {matching_dccbs}")
        
        if not matching_dccbs and user_dccbs:
            # Add missing DCCBs to Associate
            new_dccbs = list(associate_dccbs.union(user_dccbs))
            associate.multiple_dccb = new_dccbs
            associate.save()
            fixes_applied.append(f"Added missing DCCBs to Associate: {user_dccbs}")
            print(f"   ✓ FIXED: Added missing DCCBs to Associate")
    
    # Summary
    print(f"\n=== DIAGNOSTIC SUMMARY ===")
    print(f"Issues Found: {len(issues_found)}")
    for issue in issues_found:
        print(f"  - {issue}")
    
    print(f"\nFixes Applied: {len(fixes_applied)}")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    # Final status
    if len(issues_found) == 0:
        print(f"\n✅ SYSTEM STATUS: HEALTHY")
        print("Travel request system should be working correctly.")
    else:
        print(f"\n⚠️  SYSTEM STATUS: ISSUES DETECTED")
        print("Some issues may require manual intervention.")
    
    # Login instructions
    associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
    if associate:
        print(f"\n=== LOGIN INSTRUCTIONS ===")
        print(f"Associate Login:")
        print(f"  Employee ID: {associate.employee_id}")
        print(f"  Password: Associate123!")
        print(f"  URL: /auth/associate-dashboard/")
        
        print(f"\nField Officer Login:")
        print(f"  Employee ID: MGJ00002")
        print(f"  Password: (use existing password)")
        print(f"  URL: /auth/field-dashboard/")

if __name__ == '__main__':
    diagnose_and_fix()