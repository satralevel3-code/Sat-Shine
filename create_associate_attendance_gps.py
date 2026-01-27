import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone
from datetime import time

# Find Associate user
associate = CustomUser.objects.filter(designation='Associate').first()

if not associate:
    print("ERROR: No Associate user found!")
    print("Run: python manage.py seed_production_data")
    exit(1)

print(f"Found Associate: {associate.employee_id} - {associate.first_name} {associate.last_name}")

# Check if already marked today
today = timezone.localdate()
existing = Attendance.objects.filter(user=associate, date=today).first()

if existing:
    print(f"\nAttendance already marked for today:")
    print(f"  Status: {existing.status}")
    print(f"  GPS: {existing.latitude}, {existing.longitude}")
    print(f"  Check-in: {existing.check_in_time}")
else:
    # Create attendance with GPS
    attendance = Attendance.objects.create(
        user=associate,
        date=today,
        status='present',
        latitude=23.0225,  # Ahmedabad
        longitude=72.5714,
        check_in_time=time(9, 0),
        location_address='Test Location - Ahmedabad',
        location_accuracy=10.0,
        marked_at=timezone.now()
    )
    print(f"\nCreated attendance record:")
    print(f"  Date: {attendance.date}")
    print(f"  Status: {attendance.status}")
    print(f"  GPS: {attendance.latitude}, {attendance.longitude}")
    print(f"  Check-in: {attendance.check_in_time}")

# Verify GPS data
gps_count = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).count()

print(f"\nTotal attendance records with GPS: {gps_count}")
