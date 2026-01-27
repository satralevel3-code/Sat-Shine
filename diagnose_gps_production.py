import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone

print("=" * 70)
print("PRODUCTION GPS DIAGNOSTIC")
print("=" * 70)

# Check all users
all_users = CustomUser.objects.all()
print(f"\n1. TOTAL USERS: {all_users.count()}")
for user in all_users:
    print(f"   - {user.employee_id}: {user.first_name} {user.last_name} ({user.designation})")

# Check all attendance
all_attendance = Attendance.objects.all()
print(f"\n2. TOTAL ATTENDANCE RECORDS: {all_attendance.count()}")

# Check attendance with GPS
gps_attendance = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
)
print(f"\n3. ATTENDANCE WITH GPS: {gps_attendance.count()}")

if gps_attendance.exists():
    for att in gps_attendance.order_by('-date')[:10]:
        print(f"   - {att.date} | {att.user.employee_id} ({att.user.designation}) | {att.status} | GPS: {att.latitude}, {att.longitude}")
else:
    print("   NO GPS DATA FOUND!")

# Check today's attendance
today = timezone.localdate()
today_attendance = Attendance.objects.filter(date=today)
print(f"\n4. TODAY'S ATTENDANCE ({today}): {today_attendance.count()}")
for att in today_attendance:
    gps = f"GPS: {att.latitude}, {att.longitude}" if att.latitude else "NO GPS"
    print(f"   - {att.user.employee_id} ({att.user.designation}) | {att.status} | {gps}")

# Check Associate specifically
associate_users = CustomUser.objects.filter(designation='Associate')
print(f"\n5. ASSOCIATE USERS: {associate_users.count()}")
for user in associate_users:
    att_count = Attendance.objects.filter(user=user).count()
    gps_count = Attendance.objects.filter(user=user, latitude__isnull=False).count()
    print(f"   - {user.employee_id}: {att_count} attendance records, {gps_count} with GPS")

print("\n" + "=" * 70)
print("DIAGNOSIS:")
if gps_attendance.count() == 0:
    print("❌ NO GPS DATA - Run: railway run python manage.py seed_production_data")
else:
    print(f"✅ Found {gps_attendance.count()} GPS records")
print("=" * 70)
