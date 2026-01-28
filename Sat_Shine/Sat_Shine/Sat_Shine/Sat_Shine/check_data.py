from authe.models import Attendance
from django.utils import timezone

print("=== ATTENDANCE DATA CHECK ===")
total = Attendance.objects.count()
with_gps = Attendance.objects.exclude(latitude__isnull=True).count()
today = timezone.localdate()
today_total = Attendance.objects.filter(date=today).count()
today_gps = Attendance.objects.filter(date=today).exclude(latitude__isnull=True).count()

print(f"Total attendance records: {total}")
print(f"Records with GPS: {with_gps}")
print(f"Today's attendance: {today_total}")
print(f"Today's GPS records: {today_gps}")

print("\n=== SAMPLE GPS DATA ===")
for a in Attendance.objects.exclude(latitude__isnull=True)[:5]:
    print(f"{a.user.employee_id}: {a.date} - {a.latitude}, {a.longitude} ({a.status})")