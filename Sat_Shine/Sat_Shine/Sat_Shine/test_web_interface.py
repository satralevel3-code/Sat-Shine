#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from authe.models import CustomUser, Attendance
from django.utils import timezone

def test_web_interface():
    print("=== Testing Web Interface ===")
    
    # Get test user
    user = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'DC', 'Support'],
        is_active=True
    ).first()
    
    if not user:
        print("No test user found")
        return
    
    print(f"Testing with user: {user.employee_id} ({user.designation})")
    
    # Create test client
    client = Client()
    
    # Test login
    client.force_login(user)
    print("SUCCESS: User logged in")
    
    # Test mark attendance page (GET)
    response = client.get('/auth/mark-attendance/')
    print(f"GET /mark-attendance/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("SUCCESS: Mark attendance page loads")
        
        # Check if enhanced template is used
        if 'check-in-form' in response.content.decode():
            print("SUCCESS: Enhanced check-in form detected")
        else:
            print("WARNING: Enhanced form not detected")
    
    # Clean existing attendance
    today = timezone.localdate()
    Attendance.objects.filter(user=user, date=today).delete()
    
    # Test check-in via POST (JSON)
    checkin_data = {
        'status': 'present',
        'workplace': 'DCCB',
        'travel_required': False,
        'latitude': 23.0225,
        'longitude': 72.5714,
        'accuracy': 10
    }
    
    response = client.post(
        '/auth/mark-attendance/',
        data=json.dumps(checkin_data),
        content_type='application/json'
    )
    
    print(f"POST /mark-attendance/ (check-in) - Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("SUCCESS: Check-in via API works")
            print(f"Response: {result.get('message')}")
        else:
            print(f"ERROR: {result.get('error')}")
    
    # Test check-out via POST
    checkout_data = {
        'latitude': 23.0225,
        'longitude': 72.5714,
        'accuracy': 10
    }
    
    response = client.post(
        '/auth/check-out/',
        data=json.dumps(checkout_data),
        content_type='application/json'
    )
    
    print(f"POST /check-out/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("SUCCESS: Check-out via API works")
            print(f"Response: {result.get('message')}")
        else:
            print(f"ERROR: {result.get('error')}")
    
    # Verify final attendance record
    attendance = Attendance.objects.filter(user=user, date=today).first()
    if attendance:
        print(f"\\nFinal Attendance Record:")
        print(f"- Status: {attendance.status}")
        print(f"- Check-in: {attendance.check_in_time}")
        print(f"- Check-out: {attendance.check_out_time}")
        print(f"- Workplace: {attendance.workplace}")
        print(f"- Travel Required: {attendance.travel_required}")
        print(f"- GPS: {attendance.latitude}, {attendance.longitude}")

def test_access_control():
    print("\\n=== Testing Access Control ===")
    
    # Test with non-eligible designation
    admin_user = CustomUser.objects.filter(role='admin').first()
    if admin_user:
        client = Client()
        client.force_login(admin_user)
        
        response = client.get('/auth/mark-attendance/')
        print(f"Admin access to mark-attendance: {response.status_code}")
        
        if response.status_code == 403:
            print("SUCCESS: Admin correctly denied access")
        elif response.status_code == 302:
            print("SUCCESS: Admin redirected (access denied)")
        else:
            print("WARNING: Admin may have unexpected access")

if __name__ == '__main__':
    test_web_interface()
    test_access_control()
    print("\\n=== Web Interface Test Complete ===")