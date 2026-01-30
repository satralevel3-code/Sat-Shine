#!/usr/bin/env python
"""
Fix field officer passwords for login issues
"""
import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from authe.models import CustomUser

def fix_field_officer_passwords():
    """Reset passwords for all field officers"""
    field_officers = CustomUser.objects.filter(role='field_officer')
    
    print(f"Found {field_officers.count()} field officers")
    
    for officer in field_officers:
        # Set password to employee_id (same as username)
        officer.set_password(officer.employee_id)
        officer.save()
        print(f"Fixed password for {officer.employee_id} ({officer.first_name} {officer.last_name})")
    
    print("\n[OK] All field officer passwords have been reset to their Employee IDs")
    print("Field officers can now login with:")
    print("Username: [Employee ID]")
    print("Password: [Employee ID]")

if __name__ == '__main__':
    fix_field_officer_passwords()