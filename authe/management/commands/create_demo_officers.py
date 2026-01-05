from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from authe.models import CustomUser, Attendance
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create demo field officers with sample data for production'

    def handle(self, *args, **options):
        demo_officers = [
            {
                'employee_id': 'MGJ00001',
                'first_name': 'RAJESH',
                'last_name': 'PATEL',
                'designation': 'DC',
                'contact_number': '9876543201',
                'dccb': 'AHMEDABAD',
                'reporting_manager': 'SURESH KUMAR',
                'email': 'rajesh.patel@satshine.com'
            },
            {
                'employee_id': 'MGJ00002', 
                'first_name': 'PRIYA',
                'last_name': 'SHAH',
                'designation': 'MT',
                'contact_number': '9876543202',
                'dccb': 'SURAT',
                'reporting_manager': 'RAJESH PATEL',
                'email': 'priya.shah@satshine.com'
            },
            {
                'employee_id': 'MGJ00003',
                'first_name': 'AMIT',
                'last_name': 'DESAI',
                'designation': 'MT', 
                'contact_number': '9876543203',
                'dccb': 'BARODA',
                'reporting_manager': 'RAJESH PATEL',
                'email': 'amit.desai@satshine.com'
            },
            {
                'employee_id': 'MGJ00004',
                'first_name': 'KAVITA',
                'last_name': 'JOSHI',
                'designation': 'Support',
                'contact_number': '9876543204', 
                'dccb': 'RAJKOT',
                'reporting_manager': 'RAJESH PATEL',
                'email': 'kavita.joshi@satshine.com'
            },
            {
                'employee_id': 'MGJ00005',
                'first_name': 'VIKRAM',
                'last_name': 'MEHTA',
                'designation': 'MT',
                'contact_number': '9876543205',
                'dccb': 'JAMNAGAR', 
                'reporting_manager': 'RAJESH PATEL',
                'email': 'vikram.mehta@satshine.com'
            }
        ]

        created_count = 0
        updated_count = 0

        for officer_data in demo_officers:
            employee_id = officer_data['employee_id']
            
            # Check if user already exists
            user, created = CustomUser.objects.get_or_create(
                employee_id=employee_id,
                defaults={
                    **officer_data,
                    'password': make_password('Demo@123'),
                    'role': 'field_officer',
                    'is_active': True,
                    'is_staff': False,
                    'is_demo_user': True,
                    'username': employee_id
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created demo officer: {employee_id} - {officer_data["first_name"]} {officer_data["last_name"]}')
                )
                
                # Create sample attendance data for last 30 days
                self.create_sample_attendance(user)
                
            else:
                # Update existing user with latest data
                for key, value in officer_data.items():
                    setattr(user, key, value)
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated existing officer: {employee_id} - {officer_data["first_name"]} {officer_data["last_name"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Summary: {created_count} created, {updated_count} updated')
        )
        self.stdout.write(
            self.style.SUCCESS('Demo officers are now protected in production database')
        )
        self.stdout.write(
            self.style.SUCCESS('Default password for all demo officers: Demo@123')
        )

    def create_sample_attendance(self, user):
        """Create realistic sample attendance data for the user"""
        today = timezone.now().date()
        
        for i in range(30):
            date = today - timedelta(days=i)
            
            # Skip Sundays (weekday 6)
            if date.weekday() == 6:
                continue
                
            # 90% attendance rate
            if random.random() < 0.9:
                # Random check-in time between 8:30 AM and 10:00 AM
                check_in_hour = random.randint(8, 9)
                check_in_minute = random.randint(0 if check_in_hour == 8 else 0, 59 if check_in_hour == 8 else 59)
                if check_in_hour == 8 and check_in_minute < 30:
                    check_in_minute = random.randint(30, 59)
                
                # Random check-out time between 5:30 PM and 7:00 PM  
                check_out_hour = random.randint(17, 18)
                check_out_minute = random.randint(30 if check_out_hour == 17 else 0, 59)
                
                status = 'present'
                if check_in_hour >= 10 or (check_in_hour == 9 and check_in_minute > 30):
                    # Late arrival - sometimes half day
                    status = 'half_day' if random.random() < 0.3 else 'present'
                
                # Create attendance record
                attendance, created = Attendance.objects.get_or_create(
                    user=user,
                    date=date,
                    defaults={
                        'status': status,
                        'check_in_time': f'{check_in_hour:02d}:{check_in_minute:02d}',
                        'check_out_time': f'{check_out_hour:02d}:{check_out_minute:02d}',
                        'check_in_location': f'{23.0225 + random.uniform(-0.1, 0.1)},{72.5714 + random.uniform(-0.1, 0.1)}',
                        'location_address': f'{user.dccb} Office Location',
                        'is_location_valid': True,
                        'distance_from_office': random.uniform(50, 200)
                    }
                )