#!/usr/bin/env python
"""
Database validation script for SAT-SHINE production deployment
Ensures PostgreSQL is properly connected and data persists
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from django.db import connection
from authe.models import CustomUser, Attendance

def check_database():
    """Validate database connection and data persistence"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection: SUCCESS")
        
        # Check database type
        db_vendor = connection.vendor
        print(f"📊 Database type: {db_vendor.upper()}")
        
        if db_vendor == 'sqlite':
            print("🚨 WARNING: Using SQLite - data will be lost on deployment!")
            return False
        elif db_vendor == 'postgresql':
            print("✅ PostgreSQL detected - data will persist")
        
        # Check existing data
        user_count = CustomUser.objects.count()
        attendance_count = Attendance.objects.count()
        
        print(f"👥 Total users: {user_count}")
        print(f"📅 Total attendance records: {attendance_count}")
        
        # Check field officers specifically
        field_officers = CustomUser.objects.filter(role='field_officer').count()
        print(f"🏢 Field Officers: {field_officers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)