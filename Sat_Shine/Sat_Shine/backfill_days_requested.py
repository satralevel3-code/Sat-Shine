#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import LeaveRequest

updated = 0

for leave in LeaveRequest.objects.filter(days_requested__isnull=True):
    total_days = (leave.end_date - leave.start_date).days + 1
    
    if leave.duration == 'half_day':
        leave.days_requested = 0.5
    else:
        leave.days_requested = float(total_days)
    
    leave.save()
    updated += 1

print(f"Backfill completed. Updated records: {updated}")

# Verification
null_count = LeaveRequest.objects.filter(days_requested__isnull=True).count()
total_count = LeaveRequest.objects.count()

print(f"Verification - NULL records remaining: {null_count}")
print(f"Total LeaveRequest records: {total_count}")