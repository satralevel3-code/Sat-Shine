#!/usr/bin/env python
"""
Simple health check script to verify Django setup
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')

try:
    django.setup()
    print("[OK] Django setup successful")
    
    # Test database connection
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("[OK] Database connection successful")
    
    # Test static files
    from django.conf import settings
    print(f"[OK] Static files configured: {settings.STATIC_ROOT}")
    
    print("[OK] All checks passed - Application should start successfully")
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)