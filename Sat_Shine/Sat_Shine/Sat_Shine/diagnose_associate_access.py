#!/usr/bin/env python
"""
Diagnostic script to check Associate travel approval access
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest

def diagnose_associate_access():
    print("=== Associate Travel Approval Diagnostic ===\n")
    
    # Check MGJ00002 (ABHISHEK KENE)
    try:
        associate = CustomUser.objects.get(employee_id='MGJ00002')
        print(f"Associate Found: {associate.employee_id}")
        print(f"Name: {associate.first_name} {associate.last_name}")
        print(f"Designation: '{associate.designation}'")
        print(f"Role: '{associate.role}'")
        print(f"Can Approve Travel: {associate.can_approve_travel}")
        print(f"Is Active: {associate.is_active}")
        print(f"Multiple DCCBs: {associate.multiple_dccb}")
        print()
        
        # Check other users' DCCBs
        print("Other Users' DCCBs:")
        other_users = CustomUser.objects.filter(employee_id__in=['MGJ00001', 'MGJ00003', 'MGJ00005'])
        for user in other_users:
            print(f"  {user.employee_id} ({user.designation}): DCCB = '{user.dccb}'")
        print()
        
        # Check travel requests
        print("Travel Requests:")
        travel_requests = TravelRequest.objects.all().order_by('-created_at')[:10]
        for tr in travel_requests:
            print(f"  ID: {tr.id}, From: {tr.user.employee_id}, DCCB: {tr.user.dccb}, Status: {tr.status}")
            print(f"    Request To: {tr.request_to.employee_id if tr.request_to else 'None'}")
        print()
        
        # Check if Associate can see travel requests
        if associate.designation == 'Associate' and associate.multiple_dccb:
            user_dccbs = associate.multiple_dccb
            print(f"Associate's assigned DCCBs: {user_dccbs}")
            
            # Check which travel requests should be visible
            visible_requests = TravelRequest.objects.filter(
                user__dccb__in=user_dccbs
            ).order_by('-created_at')
            
            print(f"Travel requests visible to Associate: {visible_requests.count()}")
            for tr in visible_requests:
                print(f"  {tr.user.employee_id} ({tr.user.dccb}) - {tr.status}")
        
    except CustomUser.DoesNotExist:
        print("ERROR: MGJ00002 not found!")
        return
    
    # Check Associate access logic
    print("\n=== Access Logic Check ===")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    print(f"Total Associates found: {associates.count()}")
    
    for assoc in associates:
        print(f"\nAssociate: {assoc.employee_id}")
        print(f"  Designation: '{assoc.designation}'")
        print(f"  Can Approve Travel: {assoc.can_approve_travel}")
        print(f"  Multiple DCCBs: {assoc.multiple_dccb}")
        
        # Check URL access
        if assoc.employee_id == 'MGJ00002':
            print(f"  URL Access Check:")
            print(f"    - Should access /associate-travel-approvals/")
            print(f"    - Designation check: {'PASS' if assoc.designation == 'Associate' else 'FAIL'}")
            print(f"    - Permission check: {'PASS' if assoc.can_approve_travel else 'FAIL'}")

if __name__ == '__main__':
    diagnose_associate_access()