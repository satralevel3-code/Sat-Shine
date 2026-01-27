#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date, timedelta

sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, LeaveRequest, Attendance

def test_leave_attendance_integration():
    print("=== LEAVE ATTENDANCE INTEGRATION TEST ===")
    
    # Find a field officer
    field_officer = CustomUser.objects.filter(role='field_officer').first()
    if not field_officer:
        print("No field officer found!")
        return
    
    print(f"Testing with user: {field_officer.employee_id}")
    
    # Check for approved leave requests
    approved_leaves = LeaveRequest.objects.filter(
        user=field_officer,
        status='approved'
    ).order_by('-approved_at')[:3]
    
    print(f"Found {approved_leaves.count()} approved leave requests")
    
    for leave in approved_leaves:
        print(f"\\nLeave Request: {leave.id}")
        print(f"  Type: {leave.leave_type}")
        print(f"  Dates: {leave.start_date} to {leave.end_date}")
        print(f"  Status: {leave.status}")
        print(f"  Approved by: {leave.approved_by.employee_id if leave.approved_by else 'None'}")
        
        # Check attendance records for leave dates
        current_date = leave.start_date
        while current_date <= leave.end_date:
            attendance = Attendance.objects.filter(
                user=field_officer,
                date=current_date
            ).first()
            
            if attendance:
                print(f"  {current_date}: {attendance.status} (Leave Day: {attendance.is_leave_day}) - {attendance.remarks}")
            else:
                print(f"  {current_date}: NO ATTENDANCE RECORD")
            
            current_date += timedelta(days=1)
    
    # Check recent attendance records
    print(f"\\nRecent Attendance Records for {field_officer.employee_id}:")
    recent_attendance = Attendance.objects.filter(
        user=field_officer
    ).order_by('-date')[:10]
    
    for att in recent_attendance:
        leave_indicator = " (LEAVE)" if att.is_leave_day else ""
        print(f"  {att.date}: {att.status}{leave_indicator} - {att.remarks or 'No remarks'}")

if __name__ == "__main__":
    test_leave_attendance_integration()