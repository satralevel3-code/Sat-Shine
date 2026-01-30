#!/usr/bin/env python
"""
Fix MGJ00002 designation and setup as Associate
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

def fix_mgj00002():
    print("=== Fixing MGJ00002 Setup ===\n")
    
    try:
        user = CustomUser.objects.get(employee_id='MGJ00002')
        print(f"Current: {user.employee_id} - {user.first_name} {user.last_name}")
        print(f"Designation: {user.designation}")
        print(f"Can Approve Travel: {user.can_approve_travel}")
        print(f"Multiple DCCBs: {user.multiple_dccb}")
        print()
        
        # Update to Associate
        user.first_name = 'ABHISHEK'
        user.last_name = 'KENE'
        user.designation = 'Associate'
        user.can_approve_travel = True
        
        # Assign DCCBs that are not covered by other Associates
        # Current Associates cover:
        # MGJ00080: AHMEDABAD, JUNAGADH, AMRELI
        # MGJ00056: BARODA, SABARKANTHA, BHARUCH
        # Remaining: BANASKANTHA, BHAVNAGAR, JAMNAGAR, KHEDA, KODINAR, KUTCH, MAHESANA, PANCHMAHAL, RAJKOT, SURAT, SURENDRANAGAR, VALSAD
        
        user.multiple_dccb = ['KHEDA', 'SURAT', 'RAJKOT', 'MAHESANA', 'PANCHMAHAL', 'BANASKANTHA']
        user.save()
        
        print("UPDATED:")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Designation: {user.designation}")
        print(f"Can Approve Travel: {user.can_approve_travel}")
        print(f"Assigned DCCBs: {user.multiple_dccb}")
        print()
        
        # Check which travel requests should now be visible
        from authe.models import TravelRequest
        visible_requests = TravelRequest.objects.filter(
            user__dccb__in=user.multiple_dccb,
            status='pending'
        )
        
        print(f"Pending travel requests now visible to MGJ00002: {visible_requests.count()}")
        for tr in visible_requests:
            print(f"  {tr.user.employee_id} ({tr.user.dccb}) - {tr.from_date} to {tr.to_date}")
        
        print("\n✅ MGJ00002 is now properly configured as Associate!")
        
    except CustomUser.DoesNotExist:
        print("ERROR: MGJ00002 not found!")

if __name__ == '__main__':
    fix_mgj00002()