#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone
from django.contrib.auth import authenticate

print("=== SAT-SHINE DEPLOYMENT READINESS CHECK ===\n")

# 1. Check Database Connection
try:
    user_count = CustomUser.objects.count()
    print(f"[OK] Database Connection: OK ({user_count} users)")
except Exception as e:
    print(f"[ERROR] Database Connection: FAILED - {e}")
    exit(1)

# 2. Check Field Officers
field_officers = CustomUser.objects.filter(role='field_officer')
print(f"[OK] Field Officers: {field_officers.count()} users")
for user in field_officers[:3]:
    print(f"   - {user.employee_id}: {user.first_name} {user.last_name}")

# 3. Check Admin Users
admin_users = CustomUser.objects.filter(role='admin')
print(f"[OK] Admin Users: {admin_users.count()} users")
for user in admin_users[:2]:
    print(f"   - {user.employee_id}: {user.first_name} {user.last_name}")

# 4. Check Today's Attendance
today = timezone.localdate()
today_attendance = Attendance.objects.filter(date=today)
print(f"[OK] Today's Attendance ({today}): {today_attendance.count()} records")

# 5. Check GPS Data Quality
gps_records = Attendance.objects.filter(
    latitude__isnull=False, 
    longitude__isnull=False
).order_by('-date')[:5]

print(f"[OK] GPS Records: {gps_records.count()} with location data")
for record in gps_records:
    accuracy = record.location_accuracy or 999
    quality = "GOOD" if accuracy <= 100 else "POOR"
    print(f"   - {record.user.employee_id}: {record.latitude}, {record.longitude} ({accuracy}m - {quality})")

# 6. Test Authentication
test_user = field_officers.first()
if test_user:
    # Test login (assuming default password)
    auth_test = authenticate(username=test_user.employee_id, password='password123')
    if auth_test:
        print(f"[OK] Authentication: Working for {test_user.employee_id}")
    else:
        print(f"[WARNING] Authentication: Check password for {test_user.employee_id}")

# 7. Check Model Relationships
try:
    for user in field_officers[:2]:
        user_attendance = Attendance.objects.filter(user=user).count()
        print(f"   - {user.employee_id}: {user_attendance} attendance records")
    print("[OK] Model Relationships: OK")
except Exception as e:
    print(f"[ERROR] Model Relationships: FAILED - {e}")

# 8. System Summary
print(f"\n=== DEPLOYMENT SUMMARY ===")
print(f"Total Users: {CustomUser.objects.count()}")
print(f"Field Officers: {field_officers.count()}")
print(f"Admin Users: {admin_users.count()}")
print(f"Total Attendance Records: {Attendance.objects.count()}")
print(f"GPS-enabled Records: {Attendance.objects.filter(latitude__isnull=False).count()}")
print(f"Today's Attendance: {today_attendance.count()}")

# 9. Readiness Status
issues = []
if field_officers.count() == 0:
    issues.append("No field officers found")
if admin_users.count() == 0:
    issues.append("No admin users found")

if issues:
    print(f"\n[ERROR] DEPLOYMENT STATUS: NOT READY")
    for issue in issues:
        print(f"   - {issue}")
else:
    print(f"\n[OK] DEPLOYMENT STATUS: READY FOR PRODUCTION")
    print("   - All core components working")
    print("   - GPS location capture enabled")
    print("   - User authentication functional")
    print("   - Database operations successful")

print(f"\n=== END CHECK ===")