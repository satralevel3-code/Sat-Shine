import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance
from django.utils import timezone

today = timezone.localdate()
today_att = Attendance.objects.filter(date=today)

print("TODAY'S ATTENDANCE WITH GPS CHECK")
print("=" * 60)
print(f"Date: {today}")
print(f"Total records: {today_att.count()}")
print()

for att in today_att:
    has_gps = "YES" if (att.latitude and att.longitude) else "NO"
    print(f"{att.user.employee_id} ({att.user.designation:10}) | {att.status:8} | GPS: {has_gps:3} | Lat: {att.latitude} | Lng: {att.longitude}")

print()
print("GPS SUMMARY:")
with_gps = today_att.filter(latitude__isnull=False, longitude__isnull=False).count()
without_gps = today_att.filter(latitude__isnull=True).count()
print(f"  With GPS: {with_gps}")
print(f"  Without GPS: {without_gps}")
