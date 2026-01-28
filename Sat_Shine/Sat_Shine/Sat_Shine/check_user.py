#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Check user MGJ00025
user = CustomUser.objects.filter(employee_id='MGJ00025').first()
if user:
    print(f"User: {user.employee_id}")
    print(f"Role: {user.role}")
    print(f"Designation: {user.designation}")
    print(f"Active: {user.is_active}")
else:
    print("User MGJ00025 not found")