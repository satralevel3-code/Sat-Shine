#!/usr/bin/env python
"""
Data backup and restore utility for SAT-SHINE
Prevents data loss during deployments
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

from authe.models import CustomUser, Attendance, LeaveRequest, Holiday

def backup_data():
    """Backup all critical data to JSON files"""
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Backup Users
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
                'password': user.password  # Keep hashed password
            })
        
        with open(backup_dir / f'users_{timestamp}.json', 'w') as f:
            json.dump(users_data, f, indent=2)
        
        # Backup Attendance
        attendance_data = []
        for att in Attendance.objects.all():
            attendance_data.append({
                'user_id': att.user.employee_id,
                'date': att.date.isoformat(),
                'status': att.status,
                'check_in_time': att.check_in_time.isoformat() if att.check_in_time else None,
                'check_out_time': att.check_out_time.isoformat() if att.check_out_time else None,
                'check_in_location': str(att.check_in_location) if att.check_in_location else None,
                'location_address': att.location_address,
                'location_accuracy': att.location_accuracy,
                'is_location_valid': att.is_location_valid,
                'distance_from_office': att.distance_from_office,
                'remarks': att.remarks,
                'marked_at': att.marked_at.isoformat()
            })
        
        with open(backup_dir / f'attendance_{timestamp}.json', 'w') as f:
            json.dump(attendance_data, f, indent=2)
        
        # Backup Leave Requests
        leaves_data = []
        for leave in LeaveRequest.objects.all():
            leaves_data.append({
                'user_id': leave.user.employee_id,
                'leave_type': leave.leave_type,
                'duration': leave.duration,
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'days_requested': float(leave.days_requested),
                'reason': leave.reason,
                'status': leave.status,
                'applied_at': leave.applied_at.isoformat(),
                'approved_by': leave.approved_by.employee_id if leave.approved_by else None,
                'approved_at': leave.approved_at.isoformat() if leave.approved_at else None,
                'admin_remarks': leave.admin_remarks
            })
        
        with open(backup_dir / f'leaves_{timestamp}.json', 'w') as f:
            json.dump(leaves_data, f, indent=2)
        
        print(f"[OK] Data backed up successfully to backups/ directory with timestamp {timestamp}")
        return timestamp
        
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return None

def restore_data(timestamp=None):
    """Restore data from backup files"""
    backup_dir = BASE_DIR / 'backups'
    
    if not timestamp:
        # Find latest backup
        backup_files = list(backup_dir.glob('users_*.json'))
        if not backup_files:
            print("[ERROR] No backup files found")
            return False
        
        latest_file = max(backup_files, key=lambda x: x.stat().st_mtime)
        timestamp = latest_file.stem.split('_', 1)[1]
    
    try:
        # Restore Users
        users_file = backup_dir / f'users_{timestamp}.json'
        if users_file.exists():
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            for user_data in users_data:
                user, created = CustomUser.objects.get_or_create(
                    employee_id=user_data['employee_id'],
                    defaults=user_data
                )
                if not created:
                    # Update existing user
                    for key, value in user_data.items():
                        if key != 'employee_id':
                            setattr(user, key, value)
                    user.save()
        
        print(f"[OK] Data restored successfully from timestamp {timestamp}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        return False

def list_backups():
    """List available backups"""
    backup_dir = BASE_DIR / 'backups'
    backup_files = list(backup_dir.glob('users_*.json'))
    
    if not backup_files:
        print("[INFO] No backups found")
        return
    
    print("[INFO] Available backups:")
    for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        timestamp = backup_file.stem.split('_', 1)[1]
        size = backup_file.stat().st_size
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  - {timestamp} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_backup.py [backup|restore|list] [timestamp]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'backup':
        backup_data()
    elif command == 'restore':
        timestamp = sys.argv[2] if len(sys.argv) > 2 else None
        restore_data(timestamp)
    elif command == 'list':
        list_backups()
    else:
        print("Invalid command. Use: backup, restore, or list")