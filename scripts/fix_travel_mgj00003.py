#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest, Attendance
from datetime import date

def fix_travel_approved_mgj00003():
    print("=== Fixing travel_approved for MGJ00003 ===")
    
    # Get user MGJ00003
    user = CustomUser.objects.get(employee_id='MGJ00003')
    
    # Get approved travel requests
    approved_travels = TravelRequest.objects.filter(
        user=user,
        status='approved'
    )
    
    for travel in approved_travels:
        print(f"Processing travel request: {travel.from_date} to {travel.to_date}")
        
        current_date = travel.from_date
        while current_date <= travel.to_date:
            # Update attendance record
            attendance = Attendance.objects.filter(
                user=user,
                date=current_date
            ).first()
            
            if attendance:
                print(f"  Updating attendance for {current_date}")
                print(f"    Before: travel_approved = {attendance.travel_approved}")
                attendance.travel_approved = True
                attendance.save()
                print(f"    After: travel_approved = {attendance.travel_approved}")
            else:
                print(f"  No attendance record found for {current_date}")
            
            current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 31 else current_date.replace(month=current_date.month + 1, day=1)
            if current_date > travel.to_date:
                break

if __name__ == '__main__':
    fix_travel_approved_mgj00003()