import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone

print("=" * 60)
print("ASSOCIATE GPS ATTENDANCE DIAGNOSTIC")
print("=" * 60)

# Find Associate users
associates = CustomUser.objects.filter(designation='Associate')
print(f"\n1. ASSOCIATE USERS: {associates.count()}")
for user in associates:
    print(f"   - {user.employee_id}: {user.first_name} {user.last_name}")

# Check their attendance records
print(f"\n2. ASSOCIATE ATTENDANCE RECORDS:")
for user in associates:
    attendance_records = Attendance.objects.filter(user=user).order_by('-date')[:5]
    print(f"\n   {user.employee_id} - Last 5 records:")
    
    if not attendance_records.exists():
        print("      No attendance records found")
        continue
    
    for record in attendance_records:
        gps_status = "✓ GPS" if (record.latitude and record.longitude) else "✗ NO GPS"
        print(f"      {record.date} | {record.status:10} | {gps_status:10} | Lat: {record.latitude} | Lng: {record.longitude}")

# Check today's attendance
print(f"\n3. TODAY'S ATTENDANCE WITH GPS:")
today = timezone.localdate()
today_gps = Attendance.objects.filter(
    date=today,
    latitude__isnull=False,
    longitude__isnull=False
).select_related('user')

print(f"   Total records with GPS: {today_gps.count()}")
for record in today_gps:
    print(f"   - {record.user.employee_id} ({record.user.designation}): {record.status} | GPS: {record.latitude}, {record.longitude}")

# Check all attendance with GPS (any date)
print(f"\n4. ALL ATTENDANCE RECORDS WITH GPS:")
all_gps = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).select_related('user').order_by('-date')[:10]

print(f"   Total records with GPS: {all_gps.count()}")
for record in all_gps:
    print(f"   - {record.date} | {record.user.employee_id} ({record.user.designation}): {record.status} | GPS: {record.latitude}, {record.longitude}")

print("\n" + "=" * 60)
