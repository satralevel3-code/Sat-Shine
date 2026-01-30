#!/usr/bin/env python
import os
import django
import math

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance

print("=== GPS ATTENDANCE CHECK ===\n")

# Get latest GPS records
latest = Attendance.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).order_by('-date', '-id').first()

if latest:
    print("[OK] GPS DATA FOUND")
    print(f"User: {latest.user.employee_id}")
    print(f"Date: {latest.date}")
    print(f"Coordinates: {latest.latitude}, {latest.longitude}")
    print(f"Accuracy: {latest.location_accuracy}m")
    
    # Your coordinates
    your_lat = 23.204692393007157
    your_lon = 72.63039540348785
    
    # Calculate distance
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = haversine(your_lat, your_lon, float(latest.latitude), float(latest.longitude))
    
    print(f"\n=== LOCATION VERIFICATION ===")
    print(f"Your location: {your_lat}, {your_lon}")
    print(f"Recorded location: {latest.latitude}, {latest.longitude}")
    print(f"Distance: {distance:.1f} meters")
    
    # Quality assessment
    accuracy = float(latest.location_accuracy) if latest.location_accuracy else 999
    if accuracy <= 10:
        quality = "EXCELLENT"
    elif accuracy <= 30:
        quality = "GOOD"
    elif accuracy <= 100:
        quality = "ACCEPTABLE"
    else:
        quality = "POOR"
    
    print(f"GPS Quality: {quality}")
    
    if distance <= 20:
        proximity = "SAME LOCATION [OK]"
    elif distance <= 50:
        proximity = "NEARBY [OK]"
    elif distance <= 100:
        proximity = "CLOSE AREA [WARNING]"
    else:
        proximity = "DIFFERENT LOCATION [ERROR]"
    
    print(f"Location Match: {proximity}")
    
    # Check all GPS records
    print(f"\n=== ALL GPS RECORDS ===")
    all_gps = Attendance.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('-date', '-id')
    
    for i, record in enumerate(all_gps[:5]):
        dist = haversine(your_lat, your_lon, float(record.latitude), float(record.longitude))
        print(f"{i+1}. {record.user.employee_id} - {record.date} - {dist:.1f}m away")
    
else:
    print("[ERROR] NO GPS DATA FOUND")
    print("Check if attendance was marked with location enabled")