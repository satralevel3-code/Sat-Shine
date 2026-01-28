#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Create Associate user for production testing
associate, created = CustomUser.objects.get_or_create(
    employee_id='MP0001',
    defaults={
        'email': 'associate@satshine.com',
        'first_name': 'SYSTEM',
        'last_name': 'ASSOCIATE',
        'designation': 'Associate',
        'role': 'admin',
        'contact_number': '9999999999',
        'multiple_dccb': ['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA'],
        'can_approve_travel': True,
        'role_level': 7
    }
)

if created:
    associate.set_password('Associate123!')
    associate.save()
    print(f"✓ Created Associate user: {associate.employee_id}")
else:
    print(f"✓ Associate user already exists: {associate.employee_id}")

print("Associate user ready for travel request testing!")