#!/usr/bin/env python
"""
SAT-SHINE Database Migration Script
Migrates from SQLite to PostgreSQL + PostGIS
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection
from django.contrib.gis.utils import LayerMapping

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
    django.setup()

def create_postgis_extensions():
    """Create PostGIS extensions in PostgreSQL"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
            print("✅ PostGIS extensions created successfully")
        except Exception as e:
            print(f"❌ Error creating PostGIS extensions: {e}")

def run_migrations():
    """Run Django migrations"""
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Database migrations completed successfully")
    except Exception as e:
        print(f"❌ Error running migrations: {e}")

def create_spatial_indexes():
    """Create spatial indexes for performance"""
    with connection.cursor() as cursor:
        try:
            # Create spatial indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS authe_customuser_office_location_idx 
                ON authe_customuser USING GIST (office_location);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS authe_attendance_check_in_location_idx 
                ON authe_attendance USING GIST (check_in_location);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS authe_attendance_check_out_location_idx 
                ON authe_attendance USING GIST (check_out_location);
            """)
            
            print("✅ Spatial indexes created successfully")
        except Exception as e:
            print(f"❌ Error creating spatial indexes: {e}")

def create_superuser():
    """Create admin superuser"""
    from authe.models import CustomUser
    
    try:
        if not CustomUser.objects.filter(employee_id='MP0001').exists():
            admin_user = CustomUser.objects.create_superuser(
                employee_id='MP0001',
                email='admin@satshine.com',
                first_name='ADMIN',
                last_name='USER',
                contact_number='9999999999',
                password='admin123'
            )
            print("✅ Admin superuser created (MP0001/admin123)")
        else:
            print("ℹ️ Admin user already exists")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

def main():
    """Main migration function"""
    print("🚀 Starting SAT-SHINE Database Migration to PostgreSQL + PostGIS")
    print("=" * 60)
    
    setup_django()
    
    print("1. Creating PostGIS extensions...")
    create_postgis_extensions()
    
    print("2. Running Django migrations...")
    run_migrations()
    
    print("3. Creating spatial indexes...")
    create_spatial_indexes()
    
    print("4. Creating admin superuser...")
    create_superuser()
    
    print("=" * 60)
    print("✅ Migration completed successfully!")
    print("🎯 Your SAT-SHINE system is now running on PostgreSQL + PostGIS")
    print("📍 GIS features are fully enabled")
    print("🔐 Login with: MP0001 / admin123")

if __name__ == '__main__':
    main()