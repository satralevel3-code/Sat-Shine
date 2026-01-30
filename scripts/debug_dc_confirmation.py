#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from datetime import date
from django.utils import timezone

print("=== DC CONFIRMATION ISSUE DEBUG ===")

# Get DC user
dc_user = CustomUser.objects.filter(designation='DC').first()
print(f"DC User: {dc_user.employee_id}")

# Test the confirm_team_attendance endpoint
from authe.dashboard_views import confirm_team_attendance
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
import json

# Create a mock request
factory = RequestFactory()
today = timezone.localdate()

request_data = {
    'start_date': today.isoformat(),
    'end_date': today.isoformat()
}

request = factory.post('/auth/confirm-team-attendance/', 
                      data=json.dumps(request_data),
                      content_type='application/json')
request.user = dc_user

print(f"Testing DC confirmation for date: {today}")

# Clear existing records first
team_members = CustomUser.objects.filter(
    role='field_officer',
    dccb=dc_user.dccb,
    designation__in=['MT', 'Support']
).exclude(id=dc_user.id)

print(f"Team members: {[m.employee_id for m in team_members]}")

# Clear existing attendance
Attendance.objects.filter(user__in=team_members, date=today).delete()
print("Cleared existing attendance records")

# Test the confirmation function
try:
    response = confirm_team_attendance(request)
    print(f"Response status: {response.status_code}")
    
    if hasattr(response, 'content'):
        import json
        response_data = json.loads(response.content.decode())
        print(f"Response data: {response_data}")
    
    # Check if records were created
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            print(f"{member.employee_id}: {attendance.status}, DC Confirmed: {attendance.is_confirmed_by_dc}")
        else:
            print(f"{member.employee_id}: No record created")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()