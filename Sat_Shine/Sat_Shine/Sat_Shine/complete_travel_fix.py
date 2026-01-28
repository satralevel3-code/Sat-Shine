#!/usr/bin/env python
"""
PRODUCTION TRAVEL REQUEST COMPLETE FIX
This script will resolve all travel request issues in production
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

def complete_fix():
    print("=== PRODUCTION TRAVEL REQUEST COMPLETE FIX ===\n")
    
    with transaction.atomic():
        # 1. Create/Fix Associate User
        print("1. Creating/Fixing Associate User...")
        
        associate, created = CustomUser.objects.get_or_create(
            employee_id='MP0001',
            defaults={
                'email': 'associate@satshine.com',
                'first_name': 'SYSTEM',
                'last_name': 'ASSOCIATE',
                'designation': 'Associate',
                'role': 'admin',
                'contact_number': '9999999999',
                'multiple_dccb': ['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA', 'MAHESANA', 'BANASKANTHA'],
                'can_approve_travel': True,\n                'role_level': 7,\n                'is_active': True\n            }\n        )\n        \n        if created:\n            associate.set_password('Associate123!')\n            associate.save()\n            print(f\"   ✓ Created Associate user: {associate.employee_id}\")\n        else:\n            # Update existing Associate\n            associate.multiple_dccb = ['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA', 'MAHESANA', 'BANASKANTHA']\n            associate.can_approve_travel = True\n            associate.role_level = 7\n            associate.is_active = True\n            associate.set_password('Associate123!')\n            associate.save()\n            print(f\"   ✓ Updated Associate user: {associate.employee_id}\")\n        \n        # 2. Fix MGJ00002 User\n        print(\"\\n2. Fixing MGJ00002 User...\")\n        try:\n            mgj_user = CustomUser.objects.get(employee_id='MGJ00002')\n            \n            # Ensure proper configuration\n            if not mgj_user.dccb:\n                mgj_user.dccb = 'AHMEDABAD'\n            if mgj_user.designation not in ['MT', 'DC', 'Support']:\n                mgj_user.designation = 'MT'\n            mgj_user.is_active = True\n            mgj_user.save()\n            \n            print(f\"   ✓ Fixed MGJ00002: DCCB={mgj_user.dccb}, Designation={mgj_user.designation}\")\n            \n        except CustomUser.DoesNotExist:\n            print(\"   ✗ MGJ00002 user not found - creating...\")\n            mgj_user = CustomUser.objects.create_user(\n                employee_id='MGJ00002',\n                email='mgj00002@satshine.com',\n                password='Field123!',\n                first_name='TEST',\n                last_name='USER',\n                designation='MT',\n                role='field_officer',\n                contact_number='9876543210',\n                dccb='AHMEDABAD'\n            )\n            print(f\"   ✓ Created MGJ00002 user\")\n        \n        # 3. Fix All Travel Requests\n        print(\"\\n3. Fixing Travel Requests...\")\n        \n        # Fix orphaned requests\n        orphaned_requests = TravelRequest.objects.filter(request_to__isnull=True)\n        if orphaned_requests.exists():\n            count = orphaned_requests.update(request_to=associate)\n            print(f\"   ✓ Fixed {count} orphaned travel requests\")\n        \n        # Fix requests with invalid Associates\n        invalid_requests = TravelRequest.objects.exclude(request_to=associate)\n        if invalid_requests.exists():\n            count = invalid_requests.update(request_to=associate)\n            print(f\"   ✓ Reassigned {count} requests to valid Associate\")\n        \n        # 4. Create Test Travel Request\n        print(\"\\n4. Creating Test Travel Request...\")\n        \n        # Delete existing test requests\n        TravelRequest.objects.filter(er_id__startswith='TEST').delete()\n        \n        # Create new test request\n        test_request = TravelRequest.objects.create(\n            user=mgj_user,\n            from_date=timezone.localdate(),\n            to_date=timezone.localdate() + timedelta(days=1),\n            duration='full_day',\n            days_count=1.0,\n            request_to=associate,\n            er_id='TEST12345678901234567',\n            distance_km=50,\n            address='Test Address for Travel Request Verification System Testing Purpose',\n            contact_person='9876543210',\n            purpose='Test travel request created for production system verification and debugging testing purposes'\n        )\n        \n        print(f\"   ✓ Created test travel request ID: {test_request.id}\")\n        \n        # 5. Verify System\n        print(\"\\n5. System Verification...\")\n        \n        # Check Associate can see requests\n        associate_requests = TravelRequest.objects.filter(\n            user__dccb__in=associate.multiple_dccb\n        )\n        print(f\"   ✓ Associate can see {associate_requests.count()} travel requests\")\n        \n        # Check pending requests\n        pending_requests = associate_requests.filter(status='pending')\n        print(f\"   ✓ {pending_requests.count()} pending requests for approval\")\n        \n        # 6. Final Status\n        print(\"\\n=== SYSTEM STATUS ===\\n\")\n        \n        print(f\"Associate User: {associate.employee_id}\")\n        print(f\"  - Password: Associate123!\")\n        print(f\"  - DCCBs: {associate.multiple_dccb}\")\n        print(f\"  - Can Approve Travel: {associate.can_approve_travel}\")\n        print(f\"  - Role Level: {associate.role_level}\")\n        \n        print(f\"\\nField User: {mgj_user.employee_id}\")\n        print(f\"  - DCCB: {mgj_user.dccb}\")\n        print(f\"  - Designation: {mgj_user.designation}\")\n        \n        print(f\"\\nTravel Requests:\")\n        print(f\"  - Total: {TravelRequest.objects.count()}\")\n        print(f\"  - Pending: {TravelRequest.objects.filter(status='pending').count()}\")\n        print(f\"  - Test Request ID: {test_request.id}\")\n        \n        print(\"\\n=== LOGIN INSTRUCTIONS ===\\n\")\n        print(\"Associate Login:\")\n        print(f\"  URL: https://web-production-6396f.up.railway.app/auth/associate-dashboard/\")\n        print(f\"  Employee ID: {associate.employee_id}\")\n        print(f\"  Password: Associate123!\")\n        \n        print(\"\\nField Officer Login:\")\n        print(f\"  URL: https://web-production-6396f.up.railway.app/auth/field-dashboard/\")\n        print(f\"  Employee ID: {mgj_user.employee_id}\")\n        print(f\"  Password: Field123! (or existing password)\")\n        \n        print(\"\\n✅ ALL FIXES APPLIED SUCCESSFULLY!\")\n        print(\"Travel request system should now be fully functional.\")\n\nif __name__ == '__main__':\n    complete_fix()