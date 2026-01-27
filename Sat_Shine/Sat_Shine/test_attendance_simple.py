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
    print("=== Testing Field Officer Attendance Marking ===")
    
    # Check existing users with MT, DC, Support designations
    test_users = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    )[:3]  # Test first 3 users
    
    print(f"Found {test_users.count()} eligible users for testing:")
    
    today = timezone.localdate()
    
    for user in test_users:
        print(f"\n--- Testing {user.employee_id} ({user.designation}) ---")
        
        # Check existing attendance
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing:
            print(f"Status: {existing.status}")
            if existing.check_in_time:
                print(f"Check-in: {existing.check_in_time}")
            if existing.check_out_time:
                print(f"Check-out: {existing.check_out_time}")
            else:
                print("No check-out time - can test check-out")
        else:
            print("No attendance - can test check-in")
        
        # Test attendance creation
        test_check_in(user)

def test_check_in(user):
    """Test check-in functionality"""
    today = timezone.localdate()
    
    # Clean existing for test
    Attendance.objects.filter(user=user, date=today).delete()
    
    current_time = timezone.localtime().time()
    
    try:
        # Create attendance record (simulating check-in)
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
            remarks='Test check-in via script'
        )
        print(f"SUCCESS: Check-in created - {attendance.status} at {attendance.check_in_time}")
        
        # Test check-out
        checkout_time = time(17, 30)
        attendance.check_out_time = checkout_time
        attendance.save()
        print(f"SUCCESS: Check-out added at {attendance.check_out_time}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def verify_attendance_flow():
    """Verify the attendance flow works correctly"""
    print("\n=== Verifying Attendance Flow ===")
    
    # Get a test user
    user = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    ).first()
    
    if not user:
        print("No eligible user found")
        return
    
    today = timezone.localdate()
    
    # Test different scenarios
    scenarios = [
        {'status': 'present', 'workplace': 'DCCB', 'travel': False},
        {'status': 'half_day', 'workplace': 'WFH', 'travel': False},
        {'status': 'absent', 'workplace': None, 'travel': False},
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\nTest {i+1}: {scenario['status']} scenario")
        
        # Clean existing
        Attendance.objects.filter(user=user, date=today).delete()
        
        try:
            if scenario['status'] == 'absent':
                # Absent - no additional fields
                attendance = Attendance.objects.create(
                    user=user,
                    date=today,
                    status='absent'
                )
                print(f"SUCCESS: Absent marked")
            else:
                # Present/Half Day - full fields
                attendance = Attendance.objects.create(
                    user=user,
                    date=today,
                    status=scenario['status'],
                    check_in_time=timezone.localtime().time(),
                    workplace=scenario['workplace'],
                    travel_required=scenario['travel'],
                    latitude=23.0225,
                    longitude=72.5714,
                    location_accuracy=10,
                    is_location_valid=True
                )
                print(f"SUCCESS: {scenario['status']} marked with workplace {scenario['workplace']}")
                
                # Add check-out for present/half_day
                attendance.check_out_time = time(17, 0)
                attendance.save()
                print(f"SUCCESS: Check-out added")
                
        except Exception as e:
            print(f"ERROR in scenario {i+1}: {str(e)}")

if __name__ == '__main__':
    test_attendance_marking()
    verify_attendance_flow()
    print("\n=== Test Complete ===")