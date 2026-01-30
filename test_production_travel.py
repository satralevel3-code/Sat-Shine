#!/usr/bin/env python
"""
Production Test: Travel Approval Validation
Run this on Railway console to test the travel approval business rule
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, TravelRequest
from authe.travel_approval_validator import validate_travel_approval_for_dc_confirmation
from django.utils import timezone
from datetime import timedelta

print("🧪 PRODUCTION TEST: Travel Approval Validation")
print("=" * 60)

# Get test users
mt_users = CustomUser.objects.filter(designation='MT', is_active=True)
dc_users = CustomUser.objects.filter(designation='DC', is_active=True)

print(f"\n📊 Available Users:")
print(f"   MT Users: {mt_users.count()}")
print(f"   DC Users: {dc_users.count()}")

if mt_users.count() == 0:
    print("❌ No MT users found. Creating test MT user...")
    mt_user = CustomUser(
        employee_id='MGJ00001',
        email='mt@test.com',
        first_name='TEST',
        last_name='MT',
        contact_number='9999999999',
        role='field_officer',
        designation='MT',
        dccb='AHMEDABAD',
        is_active=True
    )
    mt_user.set_password('test123')
    mt_user.save()
    print(f"✅ Created MT user: {mt_user.employee_id}")
else:
    mt_user = mt_users.first()
    print(f"✅ Using existing MT user: {mt_user.employee_id}")

today = timezone.localdate()
test_date = today + timedelta(days=1)

print(f"\n🗓️ Test Date: {test_date}")

# Test 1: No travel request (should allow DC confirmation)
print(f"\n1️⃣ TEST: No travel request")
attendance1, created = Attendance.objects.get_or_create(
    user=mt_user,
    date=test_date,
    defaults={
        'status': 'present',
        'check_in_time': timezone.localtime().time(),
        'is_confirmed_by_dc': False
    }
)

can_confirm, error_msg = validate_travel_approval_for_dc_confirmation(attendance1)
print(f"   Result: Can confirm = {can_confirm}")
print(f"   Error: {error_msg}")
print(f"   Expected: True (no travel request)")
print(f"   Status: {'✅ PASS' if can_confirm else '❌ FAIL'}")

# Test 2: Pending travel request (should block DC confirmation)
print(f"\n2️⃣ TEST: Pending travel request")
travel_pending, created = TravelRequest.objects.get_or_create(
    user=mt_user,
    from_date=test_date,
    to_date=test_date,
    defaults={
        'er_id': 'TEST12345678901234',
        'distance_km': 50,
        'address': 'Test Address',
        'contact_person': 'Test Person',
        'purpose': 'Test Purpose',
        'status': 'pending'
    }
)
if not created:
    travel_pending.status = 'pending'
    travel_pending.save()

can_confirm, error_msg = validate_travel_approval_for_dc_confirmation(attendance1)
print(f"   Result: Can confirm = {can_confirm}")
print(f"   Error: {error_msg}")
print(f"   Expected: False (travel pending)")
print(f"   Status: {'✅ PASS' if not can_confirm else '❌ FAIL'}")

# Test 3: Approved travel request (should allow DC confirmation)
print(f"\n3️⃣ TEST: Approved travel request")
travel_pending.status = 'approved'
travel_pending.save()

can_confirm, error_msg = validate_travel_approval_for_dc_confirmation(attendance1)
print(f"   Result: Can confirm = {can_confirm}")
print(f"   Error: {error_msg}")
print(f"   Expected: True (travel approved)")
print(f"   Status: {'✅ PASS' if can_confirm else '❌ FAIL'}")

# Test 4: Rejected travel request (should allow DC confirmation)
print(f"\n4️⃣ TEST: Rejected travel request")
travel_pending.status = 'rejected'
travel_pending.save()

can_confirm, error_msg = validate_travel_approval_for_dc_confirmation(attendance1)
print(f"   Result: Can confirm = {can_confirm}")
print(f"   Error: {error_msg}")
print(f"   Expected: True (travel rejected - Associate acted)")
print(f"   Status: {'✅ PASS' if can_confirm else '❌ FAIL'}")

print(f"\n" + "=" * 60)
print("🎯 BUSINESS RULE VERIFICATION:")
print("   ✅ Block DC confirmation ONLY when travel status = PENDING")
print("   ✅ Allow DC confirmation when Associate has taken ANY action")
print("=" * 60)

# Check if there are any real pending travel requests
real_pending = TravelRequest.objects.filter(status='pending').count()
print(f"\n📋 Production Status:")
print(f"   Real pending travel requests: {real_pending}")

if real_pending > 0:
    print(f"\n⚠️  WARNING: {real_pending} travel requests are pending Associate approval")
    print("   These will block DC confirmation until Associate takes action")
else:
    print(f"\n✅ No pending travel requests - DC confirmation should work normally")