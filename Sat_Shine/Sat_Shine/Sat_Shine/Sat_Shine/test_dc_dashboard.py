#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from authe.dashboard_views import field_dashboard
from datetime import date
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

print("=== DC FIELD DASHBOARD TEST ===")

# Get DC user
dc_user = CustomUser.objects.filter(designation='DC').first()
print(f"DC User: {dc_user.employee_id} - {dc_user.designation}")

# Create mock request for field dashboard
factory = RequestFactory()
request = factory.get('/field-dashboard/')
request.user = dc_user

# Add messages framework
setattr(request, 'session', {})
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

# Call field dashboard view
try:
    response = field_dashboard(request)
    print(f"Dashboard response status: {response.status_code}")
    
    # Check if response has context
    if hasattr(response, 'context_data'):
        context = response.context_data
        print(f"Can view team: {context.get('can_view_team', False)}")
        print(f"Team data: {context.get('team_data', 'None')}")
        print(f"Team members count: {len(context.get('team_members', []))}")
    
    # Check team members directly
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id)
    
    print(f"Team members found: {[m.employee_id for m in team_members]}")
    print(f"DC DCCB: {dc_user.dccb}")
    print(f"DC designation: {dc_user.designation}")
    
    # Check if DC can view team
    can_view_team = dc_user.designation == 'DC'
    print(f"Can view team (logic): {can_view_team}")
    
    # Check today's attendance for team
    today = timezone.localdate()
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            print(f"{member.employee_id}: {attendance.status}, DC Confirmed: {attendance.is_confirmed_by_dc}")
        else:
            print(f"{member.employee_id}: No attendance record")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== MANUAL DC CONFIRMATION TEST ===")

# Test manual confirmation
today = timezone.localdate()
team_members = CustomUser.objects.filter(
    role='field_officer',
    dccb=dc_user.dccb,
    designation__in=['MT', 'Support']
).exclude(id=dc_user.id)

print(f"Confirming attendance for {team_members.count()} team members on {today}")

for member in team_members:
    attendance, created = Attendance.objects.get_or_create(
        user=member,
        date=today,
        defaults={
            'status': 'absent',
            'is_confirmed_by_dc': True,
            'confirmed_by_dc': dc_user,
            'dc_confirmed_at': timezone.now(),
            'confirmation_source': 'DC'
        }
    )
    
    if not created:
        attendance.status = 'absent'
        attendance.is_confirmed_by_dc = True
        attendance.confirmed_by_dc = dc_user
        attendance.dc_confirmed_at = timezone.now()
        attendance.save()
    
    print(f"Confirmed {member.employee_id}: {attendance.status}, DC: {attendance.is_confirmed_by_dc}")

print("\nDC confirmation completed. Check field officer dashboards now.")