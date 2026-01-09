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

print("=== MT USER DASHBOARD TEST ===")

# Get MT users
mt_users = CustomUser.objects.filter(designation='MT')
today = timezone.localdate()

for mt_user in mt_users:
    print(f"\nTesting MT User: {mt_user.employee_id}")
    
    # Create mock request for field dashboard
    factory = RequestFactory()
    request = factory.get('/field-dashboard/')
    request.user = mt_user
    
    # Add messages framework
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    try:
        # Get today's attendance using the same logic as dashboard_views.py
        today_attendance = Attendance.objects.filter(user=mt_user, date=today).first()
        
        # If no attendance record exists, check if DC has confirmed this user as absent
        if not today_attendance:
            dc_confirmed_record = Attendance.objects.filter(
                user=mt_user,
                date=today,
                is_confirmed_by_dc=True
            ).first()
            
            if dc_confirmed_record:
                today_attendance = dc_confirmed_record
        
        print(f"Today's attendance: {today_attendance}")
        
        if today_attendance:
            print(f"Status: {today_attendance.status}")
            print(f"DC Confirmed: {today_attendance.is_confirmed_by_dc}")
            print(f"Confirmed by: {today_attendance.confirmed_by_dc.employee_id if today_attendance.confirmed_by_dc else 'None'}")
            
            # What should be displayed in dashboard
            if today_attendance.status == 'absent' and today_attendance.is_confirmed_by_dc:
                display = f"Absent (DC Confirmed by {today_attendance.confirmed_by_dc.employee_id})"
            else:
                display = today_attendance.get_status_display()
            
            print(f"Dashboard should show: {display}")
        else:
            print("Dashboard should show: Not Marked")
            
    except Exception as e:
        print(f"Error: {e}")

print(f"\n=== SUMMARY ===")
print(f"Date: {today}")
confirmed_records = Attendance.objects.filter(date=today, is_confirmed_by_dc=True)
print(f"DC Confirmed records: {confirmed_records.count()}")

for record in confirmed_records:
    print(f"  {record.user.employee_id}: {record.status} (confirmed by {record.confirmed_by_dc.employee_id})")

print(f"\nIf MT users still see 'Not Marked', the issue is in the frontend template logic.")