#!/usr/bin/env python
"""
Automated User Preservation System for SAT-SHINE
Ensures field officers persist across all deployments and fixes
"""
import os
import django
import json
from pathlib import Path
from datetime import datetime

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from authe.models import CustomUser, Attendance, LeaveRequest

def auto_backup_on_startup():
    """Automatically backup data when server starts"""
    try:
        backup_dir = BASE_DIR / 'persistent_data'
        backup_dir.mkdir(exist_ok=True)
        
        # Always create fresh backup on startup
        users_data = []
        for user in CustomUser.objects.all():
            users_data.append({
                'employee_id': user.employee_id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'contact_number': user.contact_number,
                'role': user.role,
                'designation': user.designation,
                'dccb': user.dccb,
                'reporting_manager': user.reporting_manager,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'password': user.password
            })
        
        with open(backup_dir / 'users_persistent.json', 'w') as f:
            json.dump(users_data, f, indent=2)
        
        print(f"[STARTUP] Backed up {len(users_data)} users to persistent storage")
        return True
        
    except Exception as e:
        print(f"[ERROR] Startup backup failed: {e}")
        return False

def restore_users_if_missing():
    """Restore users if database is empty or missing field officers"""
    try:
        field_officers_count = CustomUser.objects.filter(role='field_officer').count()
        admin_count = CustomUser.objects.filter(role='admin').count()
        
        print(f"[CHECK] Current DB: {field_officers_count} field officers, {admin_count} admins")
        
        # If no field officers or no admin, restore from backup
        if field_officers_count == 0 or admin_count == 0:
            print("[RESTORE] Missing users detected, restoring from backup...")
            
            backup_file = BASE_DIR / 'persistent_data' / 'users_persistent.json'
            if backup_file.exists():
                with open(backup_file, 'r') as f:
                    users_data = json.load(f)
                
                restored_count = 0
                for user_data in users_data:
                    user, created = CustomUser.objects.get_or_create(
                        employee_id=user_data['employee_id'],
                        defaults=user_data
                    )
                    if created:
                        restored_count += 1
                        print(f"[RESTORE] Created user: {user_data['employee_id']}")
                
                print(f"[RESTORE] Restored {restored_count} users from backup")
                return True
            else:
                print("[RESTORE] No backup file found, creating default users...")
                create_default_users()
                return True
        
        print("[CHECK] All users present, no restore needed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        return False

def create_default_users():
    """Create default admin and field officers if none exist"""
    try:
        # Create admin if not exists
        admin, created = CustomUser.objects.get_or_create(
            employee_id='MP0001',
            defaults={
                'username': 'MP0001',
                'email': 'admin@satshine.com',
                'first_name': 'ADMIN',
                'last_name': 'USER',
                'contact_number': '9999999999',
                'role': 'admin',
                'designation': 'Manager',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            print("[DEFAULT] Created admin user: MP0001")
        
        # Create sample field officers
        field_officers = [
            {'id': 'MGJ00001', 'name': 'RAJESH PATEL', 'dccb': 'AHMEDABAD', 'designation': 'MT'},
            {'id': 'MGJ00002', 'name': 'PRIYA SHAH', 'dccb': 'BARODA', 'designation': 'DC'},
            {'id': 'MGJ00003', 'name': 'AMIT DESAI', 'dccb': 'SURAT', 'designation': 'MT'},
        ]
        
        for officer in field_officers:
            first_name, last_name = officer['name'].split(' ', 1)
            user, created = CustomUser.objects.get_or_create(
                employee_id=officer['id'],
                defaults={
                    'username': officer['id'],
                    'email': f"{officer['id'].lower()}@satshine.com",
                    'first_name': first_name,
                    'last_name': last_name,
                    'contact_number': f"98765{officer['id'][-5:]}",
                    'role': 'field_officer',
                    'designation': officer['designation'],
                    'dccb': officer['dccb'],
                    'is_active': True
                }
            )
            if created:
                user.set_password(officer['id'])
                user.save()
                print(f"[DEFAULT] Created field officer: {officer['id']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Default user creation failed: {e}")
        return False

def run_preservation_system():
    """Main function to run the preservation system"""
    print("[PRESERVATION] Starting user preservation system...")
    
    # Step 1: Backup current data
    auto_backup_on_startup()
    
    # Step 2: Restore if missing
    restore_users_if_missing()
    
    # Step 3: Final verification
    field_count = CustomUser.objects.filter(role='field_officer').count()
    admin_count = CustomUser.objects.filter(role='admin').count()
    
    print(f"[FINAL] System ready: {field_count} field officers, {admin_count} admins")
    return True

if __name__ == '__main__':
    run_preservation_system()