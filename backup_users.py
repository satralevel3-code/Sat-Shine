#!/usr/bin/env python
"""
User Backup System - Prevents user data loss on Railway deployments
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

def backup_users():
    """Backup all users to JSON file"""
    users = CustomUser.objects.all()
    backup_data = []
    
    for user in users:
        backup_data.append({
            'employee_id': user.employee_id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'contact_number': user.contact_number,
            'role': user.role,
            'designation': user.designation,
            'dccb': user.dccb,
            'is_active': user.is_active,
            'role_level': user.role_level,
            'password_hash': user.password
        })
    
    with open('user_backup.json', 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"Successfully backed up {len(backup_data)} users")
    return len(backup_data)

def restore_users():
    """Restore users from backup if file exists"""
    if not os.path.exists('user_backup.json'):
        return 0
    
    with open('user_backup.json', 'r') as f:
        backup_data = json.load(f)
    
    restored = 0
    for user_data in backup_data:
        if not CustomUser.objects.filter(employee_id=user_data['employee_id']).exists():
            user = CustomUser(
                employee_id=user_data['employee_id'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                contact_number=user_data['contact_number'],
                role=user_data['role'],
                designation=user_data['designation'],
                dccb=user_data['dccb'],
                is_active=user_data['is_active'],
                role_level=user_data['role_level']
            )
            user.password = user_data['password_hash']
            user.save()
            restored += 1
    
    print(f"Successfully restored {restored} users")
    return restored

if __name__ == '__main__':
    # Always backup current users
    backup_users()