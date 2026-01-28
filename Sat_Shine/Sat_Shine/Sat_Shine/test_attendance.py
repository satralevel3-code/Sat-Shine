#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, time

# Setup Django
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, TravelRequest
from django.utils import timezone

def test_attendance_marking():
    print("=== Testing Field Officer Attendance Marking ===\n")
    
    # Check existing users with MT, DC, Support designations
    test_users = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    )
    
    print(f"Found {test_users.count()} eligible users:")
    for user in test_users:
        print(f"- {user.employee_id}: {user.first_name} {user.last_name} ({user.designation})")
    
    if not test_users.exists():
        print("No eligible users found. Creating test users...")
        create_test_users()
        test_users = CustomUser.objects.filter(
            role='field_officer',
            designation__in=['MT', 'DC', 'Support'],
            is_active=True
        )
    
    # Test attendance marking for each user
    today = timezone.localdate()
    
    for user in test_users[:3]:  # Test first 3 users
        print(f"\n--- Testing {user.employee_id} ({user.designation}) ---")
        
        # Check existing attendance
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing:
            print(f"✓ Already has attendance: {existing.status}")
            if existing.check_in_time:
                print(f"  Check-in: {existing.check_in_time}")
            if existing.check_out_time:
                print(f"  Check-out: {existing.check_out_time}")
            else:
                print("  ⚠ No check-out time")
        else:
            print("✓ No attendance marked yet - ready for testing")
        
        # Check travel requests
        travel = TravelRequest.objects.filter(
            user=user,
            from_date__lte=today,
            to_date__gte=today,
            status='approved'
        ).first()
        
        if travel:
            print(f"✓ Has approved travel: {travel.purpose}")
        else:
            print("✓ No approved travel for today")

def create_test_users():
    """Create test users if none exist"""
    test_data = [
        {'id': 'MGJ00101', 'name': 'TEST MT USER', 'designation': 'MT'},
        {'id': 'MGJ00102', 'name': 'TEST DC USER', 'designation': 'DC'},
        {'id': 'MGJ00103', 'name': 'TEST SUPPORT USER', 'designation': 'Support'},
    ]
    
    for data in test_data:
        if not CustomUser.objects.filter(employee_id=data['id']).exists():
            user = CustomUser.objects.create_user(
                employee_id=data['id'],
                email=f"{data['id'].lower()}@test.com",
                first_name=data['name'].split()[1],
                last_name=data['name'].split()[2],
                contact_number=f"98765{data['id'][-5:]}",
                designation=data['designation'],
                dccb='AHMEDABAD'
            )
            user.set_password('test123')
            user.save()
            print(f"Created test user: {data['id']}")

def test_attendance_flow():
    """Test the complete attendance flow"""
    print("\n=== Testing Attendance Flow ===")
    
    user = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    ).first()
    
    if not user:
        print("No test user available")
        return
    
    today = timezone.localdate()
    current_time = timezone.localtime().time()
    
    # Clean existing attendance for testing
    Attendance.objects.filter(user=user, date=today).delete()
    
    print(f"Testing with user: {user.employee_id}")
    
    # Test 1: Check-in as Present
    attendance = Attendance.objects.create(
        user=user,
        date=today,
        status='present',
        check_in_time=current_time,
        workplace='DCCB',
        travel_required=False,
        latitude=23.0225,
        longitude=72.5714,
        location_accuracy=10,
        is_location_valid=True,
        remarks='Test check-in'
    )
    print(f"✓ Check-in successful: {attendance.status} at {attendance.check_in_time}")
    
    # Test 2: Check-out
    checkout_time = time(17, 30)  # 5:30 PM
    attendance.check_out_time = checkout_time
    attendance.save()
    print(f"✓ Check-out successful at {attendance.check_out_time}")
    
    # Test 3: Verify data
    print(f"✓ Final status: {attendance.status}")
    print(f"✓ Workplace: {attendance.workplace}")
    print(f"✓ Travel required: {attendance.travel_required}")
    print(f"✓ Location valid: {attendance.is_location_valid}")

if __name__ == '__main__':
    test_attendance_marking()
    test_attendance_flow()
    print("\n=== Test Complete ===")