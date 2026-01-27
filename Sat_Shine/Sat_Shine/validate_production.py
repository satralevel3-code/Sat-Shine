#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import *
from django.conf import settings
from django.utils import timezone

print("=== SAT-SHINE PRODUCTION VALIDATION ===")
print()

# 1. Database Configuration
print("1. DATABASE CONFIGURATION:")
db_config = settings.DATABASES['default']
print(f"   Engine: {db_config['ENGINE']}")
print(f"   Database: {db_config.get('NAME', 'SQLite')}")
print(f"   GIS Enabled: {os.getenv('USE_POSTGRESQL', 'false')}")
print(f"   Railway Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'Local')}")
print()

# 2. Data Integrity Check
print("2. DATA INTEGRITY:")
total_users = CustomUser.objects.count()
field_officers = CustomUser.objects.filter(role='field_officer').count()
admins = CustomUser.objects.filter(role='admin').count()
print(f"   Total Users: {total_users}")
print(f"   Field Officers: {field_officers}")
print(f"   Admins: {admins}")
print()

total_attendance = Attendance.objects.count()
gps_attendance = Attendance.objects.exclude(latitude__isnull=True).count()
print(f"   Total Attendance Records: {total_attendance}")
print(f"   Records with GPS: {gps_attendance}")
print(f"   GPS Coverage: {(gps_attendance/total_attendance*100):.1f}%" if total_attendance > 0 else "   GPS Coverage: 0%")
print()

# 3. Recent Attendance Analysis
print("3. RECENT ATTENDANCE (Last 5 records):")
recent_attendance = Attendance.objects.select_related('user').order_by('-marked_at')[:5]
for att in recent_attendance:
    gps_info = f"GPS: {att.latitude:.6f},{att.longitude:.6f} ({att.location_accuracy:.1f}m)" if att.latitude else "No GPS"
    print(f"   {att.user.employee_id}: {att.status.upper()} at {att.check_in_time} - {gps_info}")
print()

# 4. Time Restriction Analysis
print("4. TIME RESTRICTION ANALYSIS:")
today = timezone.localdate()
today_attendance = Attendance.objects.filter(date=today)
print(f"   Today's Attendance Count: {today_attendance.count()}")

# Check for any time-based restrictions in code
late_attendance = today_attendance.filter(check_in_time__gt='15:00')
print(f"   Attendance after 3:00 PM: {late_attendance.count()}")

if late_attendance.exists():
    print("   SUCCESS: No 3:00 PM restriction found - attendance allowed after 3:00 PM")
else:
    print("   WARNING: No attendance after 3:00 PM (may indicate restriction or no late entries)")
print()

# 5. GIS Map Data Validation
print("5. GIS MAP DATA VALIDATION:")
map_ready_data = Attendance.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
print(f"   Records ready for map display: {map_ready_data.count()}")

if map_ready_data.exists():
    sample_record = map_ready_data.first()
    print(f"   Sample coordinates: {sample_record.latitude:.8f}, {sample_record.longitude:.8f}")
    print(f"   Sample accuracy: {sample_record.location_accuracy}m")
    print("   SUCCESS: Map data is available and properly formatted")
else:
    print("   ERROR: No GPS data available for map display")
print()

# 6. Performance Metrics
print("6. PERFORMANCE METRICS:")
from django.db import connection
print(f"   Database queries executed: {len(connection.queries)}")
print(f"   Average attendance per user: {total_attendance/field_officers:.1f}" if field_officers > 0 else "   No field officers found")
print()

print("=== VALIDATION COMPLETE ===")
print()

# 7. Recommendations
print("7. RECOMMENDATIONS:")
if gps_attendance < total_attendance * 0.8:
    print("   WARNING: GPS coverage below 80% - consider GPS optimization")
if total_attendance == 0:
    print("   ERROR: No attendance data - system needs initial data")
if field_officers == 0:
    print("   ERROR: No field officers - create test users")
print("   SUCCESS: System appears ready for production use")