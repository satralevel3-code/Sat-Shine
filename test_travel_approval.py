#!/usr/bin/env python
"""
Test script to verify travel approval system works correctly
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from datetime import date, timedelta

def test_travel_approval_system():
    print("=== SAT-SHINE Travel Approval System Test ===\n")
    
    # 1. Check Associates and their assigned DCCBs
    print("1. Associates and their assigned DCCBs:")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    
    for assoc in associates:
        dccb_list = assoc.multiple_dccb or []
        print(f"   {assoc.employee_id} ({assoc.first_name} {assoc.last_name})")
        print(f"   Assigned DCCBs: {dccb_list}")
        print(f"   Can approve travel: {assoc.can_approve_travel}")
        print()
    
    # 2. Check MT/DC/Support users and their DCCBs
    print("2. MT/DC/Support users and their DCCBs:")
    field_users = CustomUser.objects.filter(
        designation__in=['MT', 'DC', 'Support'], 
        is_active=True
    )[:10]  # Show first 10
    
    for user in field_users:
        print(f"   {user.employee_id} ({user.designation}) - DCCB: {user.dccb}")
        
        # Find which Associate can approve this user's travel
        responsible_associate = None
        for assoc in associates:
            if assoc.multiple_dccb and user.dccb in assoc.multiple_dccb:
                responsible_associate = assoc
                break
        
        if responsible_associate:
            print(f"   -> Can be approved by: {responsible_associate.employee_id}")
        else:
            print(f"   -> No Associate found for DCCB: {user.dccb}")
        print()
    
    # 3. Check recent travel requests
    print("3. Recent travel requests:")
    recent_requests = TravelRequest.objects.all().order_by('-created_at')[:5]
    
    for req in recent_requests:
        print(f"   Request ID: {req.id}")
        print(f"   From: {req.user.employee_id} ({req.user.designation}) - DCCB: {req.user.dccb}")
        print(f"   Dates: {req.from_date} to {req.to_date}")
        print(f"   Status: {req.status}")
        print(f"   Request To: {req.request_to.employee_id if req.request_to else 'Not assigned'}")
        print()
    
    # 4. Test DCCB mapping logic
    print("4. Testing DCCB mapping logic:")
    test_dccbs = ['BARODA', 'BHARUCH', 'KHEDA', 'SURAT', 'AHMEDABAD']
    
    for dccb in test_dccbs:
        responsible_associate = None
        for assoc in associates:
            if assoc.multiple_dccb and dccb in assoc.multiple_dccb:
                responsible_associate = assoc
                break
        
        if responsible_associate:
            print(f"   {dccb} -> {responsible_associate.employee_id}")
        else:
            print(f"   {dccb} -> No Associate assigned")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_travel_approval_system()