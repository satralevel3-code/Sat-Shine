#!/usr/bin/env python
"""
Test admin login functionality
"""
import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from django.contrib.auth import authenticate
from authe.models import CustomUser

def test_admin_login():
    try:
        # Test authentication
        user = authenticate(username='MP0001', password='admin123')
        
        if user:
            print(f"[OK] Authentication successful for {user.employee_id}")
            print(f"     Role: {user.role}")
            print(f"     Is Staff: {user.is_staff}")
            print(f"     Is Superuser: {user.is_superuser}")
            print(f"     Is Active: {user.is_active}")
            return True
        else:
            print("[ERROR] Authentication failed")
            
            # Check if user exists
            try:
                user = CustomUser.objects.get(employee_id='MP0001')
                print(f"[INFO] User exists: {user.employee_id}")
                print(f"       Password hash: {user.password[:20]}...")
                print(f"       Is Active: {user.is_active}")
            except CustomUser.DoesNotExist:
                print("[ERROR] User MP0001 does not exist")
            
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == '__main__':
    test_admin_login()