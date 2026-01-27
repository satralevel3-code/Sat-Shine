#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest

def debug_travel_for_mgj00003():
    print("=== DEBUG: Travel Request Issues for MGJ00003 ===")
    
    # Get user MGJ00003
    try:
        user = CustomUser.objects.get(employee_id='MGJ00003')
        print(f"User: {user.employee_id} - {user.first_name} {user.last_name}")
        print(f"DCCB: {user.dccb}")
        print(f"Designation: {user.designation}")
        print(f"Active: {user.is_active}")
    except CustomUser.DoesNotExist:
        print("ERROR: User MGJ00003 not found!")
        return
    
    print("\n=== Associates in System ===")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    for assoc in associates:
        print(f"Associate: {assoc.employee_id} - {assoc.first_name} {assoc.last_name}")
        print(f"  Multiple DCCBs: {assoc.multiple_dccb}")
        if assoc.multiple_dccb and user.dccb in assoc.multiple_dccb:
            print(f"  MATCHES {user.dccb}")
        else:
            print(f"  No match for {user.dccb}")
    
    print(f"\n=== Travel Requests for {user.employee_id} ===")
    travel_requests = TravelRequest.objects.filter(user=user).order_by('-created_at')
    if travel_requests:
        for tr in travel_requests:
            print(f"Travel Request ID: {tr.id}")
            print(f"  Dates: {tr.from_date} to {tr.to_date}")
            print(f"  Status: {tr.status}")
            print(f"  Request To: {tr.request_to.employee_id if tr.request_to else 'None'}")
            print(f"  Approved By: {tr.approved_by.employee_id if tr.approved_by else 'None'}")
            print(f"  Created: {tr.created_at}")
    else:
        print("No travel requests found")
    
    print(f"\n=== Attendance Records for {user.employee_id} (Last 7 days) ===")
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    
    from authe.models import Attendance
    attendance_records = Attendance.objects.filter(
        user=user,
        date__gte=week_ago
    ).order_by('-date')
    
    if attendance_records:
        for att in attendance_records:
            print(f"Date: {att.date}")
            print(f"  Status: {att.status}")
            print(f"  Travel Required: {att.travel_required}")
            print(f"  Travel Approved: {att.travel_approved}")
            print(f"  Remarks: {att.remarks or 'None'}")
    else:
        print("No attendance records found")

if __name__ == '__main__':
    debug_travel_for_mgj00003()