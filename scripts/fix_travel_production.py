#!/usr/bin/env python
"""
Production Travel Request Fix Script
Run this to fix common travel request issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.db import transaction

def fix_travel_requests():
    print("=== FIXING TRAVEL REQUEST ISSUES ===\n")
    
    with transaction.atomic():
        # 1. Fix Associate user configuration
        print("1. Fixing Associate user configuration...")
        
        # Find the Associate user (assuming there should be one)
        associates = CustomUser.objects.filter(designation='Associate', is_active=True)
        
        if not associates.exists():
            print("   ✗ No Associate users found!")
            print("   Creating sample Associate user...")
            
            # Create a sample Associate user if none exists
            associate = CustomUser.objects.create_user(
                employee_id='MP0001',
                email='associate@satshine.com',
                password='TempPass123!',
                first_name='SYSTEM',
                last_name='ASSOCIATE',
                designation='Associate',
                role='admin',
                contact_number='9999999999',
                multiple_dccb=['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL']
            )
            print(f"   ✓ Created Associate: {associate.employee_id}")
        else:
            # Fix existing Associate users
            for assoc in associates:
                print(f"   Checking Associate: {assoc.employee_id}")
                
                # Ensure they have multiple_dccb configured
                if not assoc.multiple_dccb:
                    assoc.multiple_dccb = ['AHMEDABAD', 'BARODA', 'BHARUCH']
                    assoc.save()
                    print(f"   ✓ Added DCCBs to {assoc.employee_id}")
                
                # Ensure they can approve travel
                if not assoc.can_approve_travel:
                    assoc.can_approve_travel = True
                    assoc.save()
                    print(f"   ✓ Enabled travel approval for {assoc.employee_id}")
        
        # 2. Fix user MGJ00002 configuration
        print(f"\n2. Fixing user MGJ00002...")
        try:
            user = CustomUser.objects.get(employee_id='MGJ00002')
            
            # Ensure user has a DCCB assigned
            if not user.dccb:
                user.dccb = 'AHMEDABAD'  # Default assignment
                user.save()
                print(f"   ✓ Assigned DCCB 'AHMEDABAD' to {user.employee_id}")
            
            # Ensure user has correct designation
            if user.designation not in ['MT', 'DC', 'Support']:
                user.designation = 'MT'  # Default for MGJ users
                user.save()
                print(f"   ✓ Set designation to 'MT' for {user.employee_id}")
                
        except CustomUser.DoesNotExist:
            print("   ✗ User MGJ00002 not found in database")
        
        # 3. Fix orphaned travel requests
        print(f"\n3. Fixing orphaned travel requests...")
        
        # Find travel requests without proper request_to assignment
        orphaned_requests = TravelRequest.objects.filter(request_to__isnull=True)
        
        if orphaned_requests.exists():
            # Get the first available Associate
            associate = CustomUser.objects.filter(
                designation='Associate', 
                is_active=True
            ).first()
            
            if associate:
                count = orphaned_requests.update(request_to=associate)
                print(f"   ✓ Fixed {count} orphaned travel requests")
            else:
                print("   ✗ No Associate available to assign orphaned requests")
        else:
            print("   ✓ No orphaned travel requests found")
        
        # 4. Ensure proper permissions
        print(f"\n4. Ensuring proper permissions...")
        
        # Update all Associates to have travel approval permissions
        associate_count = CustomUser.objects.filter(
            designation='Associate'
        ).update(
            can_approve_travel=True,
            role_level=7
        )
        print(f"   ✓ Updated {associate_count} Associates with travel permissions")
        
        print(f"\n=== FIX COMPLETED ===")
        print("Please test the travel request functionality now.")

if __name__ == '__main__':
    fix_travel_requests()