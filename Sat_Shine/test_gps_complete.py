"""
Comprehensive GPS Functionality Test
Run this to verify GPS data exists and templates work correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone

print("=" * 70)
print("GPS FUNCTIONALITY TEST")
print("=" * 70)

# Test 1: Check if users exist
print("\n[TEST 1] Users Check")
users = CustomUser.objects.all()
print(f"Total users: {users.count()}")
if users.count() == 0:
    print("ERROR: No users found!")
    print("ACTION: Run 'python manage.py seed_production_data'")
    exit(1)

for user in users:
    print(f"  - {user.employee_id}: {user.designation}")

# Test 2: Check attendance records
print("\n[TEST 2] Attendance Records Check")
attendance = Attendance.objects.all()
print(f"Total attendance records: {attendance.count()}")

if attendance.count() == 0:
    print("ERROR: No attendance records found!")
    print("ACTION: Either:")
    print("  1. Run 'python manage.py seed_production_data' (creates sample data)")
    print("  2. Mark attendance as Associate user in the app")
    exit(1)

# Test 3: Check GPS data
print("\n[TEST 3] GPS Data Check")
gps_attendance = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
)
print(f"Attendance with GPS: {gps_attendance.count()}")

if gps_attendance.count() == 0:
    print("ERROR: No GPS data found!")
    print("ISSUE: Attendance records exist but have no GPS coordinates")
    print("ACTION: Check if GPS is being captured when marking attendance")
    
    # Show records without GPS
    no_gps = Attendance.objects.filter(latitude__isnull=True)
    print(f"\nRecords WITHOUT GPS ({no_gps.count()}):")
    for att in no_gps[:5]:
        print(f"  - {att.date} | {att.user.employee_id} | {att.status}")
    exit(1)

# Test 4: Show GPS data details
print("\n[TEST 4] GPS Data Details")
for att in gps_attendance[:5]:
    print(f"  {att.date} | {att.user.employee_id} ({att.user.designation:10}) | GPS: ({att.latitude}, {att.longitude})")

# Test 5: Check today's attendance
print("\n[TEST 5] Today's Attendance")
today = timezone.localdate()
today_att = Attendance.objects.filter(date=today)
print(f"Today's records: {today_att.count()}")

if today_att.count() > 0:
    for att in today_att:
        has_gps = "YES" if (att.latitude and att.longitude) else "NO"
        print(f"  {att.user.employee_id} | {att.status} | GPS: {has_gps}")
else:
    print("  No attendance marked today")

# Test 6: Template condition check
print("\n[TEST 6] Template Condition Check")
print("Checking if location button will show...")

for att in gps_attendance[:3]:
    condition = bool(att.latitude and att.longitude)
    button_state = "ENABLED" if condition else "DISABLED"
    print(f"  {att.user.employee_id}: latitude={att.latitude}, longitude={att.longitude}")
    print(f"    -> Button will be: {button_state}")

# Test 7: API endpoint simulation
print("\n[TEST 7] API Endpoint Data Check")
print("Simulating admin_attendance_geo_data API...")

api_data = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).select_related('user')

print(f"API would return {api_data.count()} records")
if api_data.count() > 0:
    print("Sample API response:")
    for att in api_data[:2]:
        print(f"  {{")
        print(f"    'employee_id': '{att.user.employee_id}',")
        print(f"    'designation': '{att.user.designation}',")
        print(f"    'lat': {att.latitude},")
        print(f"    'lng': {att.longitude},")
        print(f"    'status': '{att.status}'")
        print(f"  }}")

# Final Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if gps_attendance.count() > 0:
    print("STATUS: PASS")
    print(f"  - {users.count()} users found")
    print(f"  - {attendance.count()} attendance records")
    print(f"  - {gps_attendance.count()} records with GPS")
    print("\nEXPECTED BEHAVIOR:")
    print("  1. Admin Attendance Map: Should show markers")
    print("  2. Today's Attendance Details: Location button should be clickable")
    print("  3. Clicking location button: Opens Google Maps")
else:
    print("STATUS: FAIL")
    print("GPS data is missing - see errors above")

print("=" * 70)
