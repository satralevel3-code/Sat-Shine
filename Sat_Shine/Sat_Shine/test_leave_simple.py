#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date, timedelta

sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, LeaveRequest, Attendance

def test_leave_integration():
    print("=== LEAVE ATTENDANCE INTEGRATION TEST ===")
    
    # Check approved leaves
    approved_leaves = LeaveRequest.objects.filter(status='approved')[:5]
    print(f"Found {approved_leaves.count()} approved leaves")
    
    for leave in approved_leaves:
        print(f"\\nLeave: {leave.user.employee_id} from {leave.start_date} to {leave.end_date}")
        
        # Check attendance for leave dates
        current_date = leave.start_date
        while current_date <= leave.end_date:
            attendance = Attendance.objects.filter(user=leave.user, date=current_date).first()
            if attendance:
                print(f"  {current_date}: {attendance.status} - {attendance.remarks}")
            else:
                print(f"  {current_date}: NO RECORD")
            current_date += timedelta(days=1)

if __name__ == "__main__":
    test_leave_integration()