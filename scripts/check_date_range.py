#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta

# Calculate the default date range
today = timezone.localdate()
from_date = (today - timedelta(days=30)).isoformat()
to_date = (today + timedelta(days=60)).isoformat()

print(f"Today: {today}")
print(f"Default From Date: {from_date}")
print(f"Default To Date: {to_date}")
print(f"\nTravel request on 2026-01-27 should be included: {from_date <= '2026-01-27' <= to_date}")
