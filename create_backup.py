#!/usr/bin/env python
"""
PRODUCTION DATABASE BACKUP SCRIPT
Creates a complete backup of the production database
"""

import os
import sys
import django
from datetime import datetime
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from django.core.management import call_command
from django.core import serializers
from authe.models import CustomUser, Attendance, TravelRequest, LeaveRequest, Notification

def create_production_backup():
    """Create complete production database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'production_backup_{timestamp}.json'
    
    print("CREATING PRODUCTION DATABASE BACKUP")
    print("=" * 50)
    
    try:
        # Method 1: Django dumpdata (complete backup)
        print("Creating complete database dump...")
        call_command('dumpdata', 
                    '--output', backup_filename,
                    '--indent', '2',
                    '--natural-foreign', 
                    '--natural-primary')
        print(f"Complete backup saved: {backup_filename}")
        
        # Method 2: Specific model backup with statistics
        print("\nCreating detailed backup with statistics...")
        
        backup_data = {
            'backup_info': {
                'timestamp': timestamp,
                'database_engine': 'SQLite',
                'backup_type': 'complete'
            },
            'statistics': {
                'total_users': CustomUser.objects.count(),
                'active_users': CustomUser.objects.filter(is_active=True).count(),
                'total_attendance': Attendance.objects.count(),
                'total_travel_requests': TravelRequest.objects.count(),
                'total_leave_requests': LeaveRequest.objects.count(),
                'total_notifications': Notification.objects.count(),
            },
            'users': list(CustomUser.objects.values()),
            'attendance': list(Attendance.objects.values()),
            'travel_requests': list(TravelRequest.objects.values()),
            'leave_requests': list(LeaveRequest.objects.values()),
            'notifications': list(Notification.objects.values()),
        }
        
        detailed_filename = f'detailed_backup_{timestamp}.json'
        with open(detailed_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"Detailed backup saved: {detailed_filename}")
        
        # Print statistics
        print("\nBACKUP STATISTICS:")
        print(f"Users: {backup_data['statistics']['total_users']}")
        print(f"Active Users: {backup_data['statistics']['active_users']}")
        print(f"Attendance Records: {backup_data['statistics']['total_attendance']}")
        print(f"Travel Requests: {backup_data['statistics']['total_travel_requests']}")
        print(f"Leave Requests: {backup_data['statistics']['total_leave_requests']}")
        print(f"Notifications: {backup_data['statistics']['total_notifications']}")
        
        print(f"\nBACKUP COMPLETED SUCCESSFULLY!")
        print(f"Files created:")
        print(f"   - {backup_filename} (Django format)")
        print(f"   - {detailed_filename} (JSON format)")
        
        return backup_filename, detailed_filename
        
    except Exception as e:
        print(f"BACKUP FAILED: {str(e)}")
        return None, None

if __name__ == '__main__':
    create_production_backup()