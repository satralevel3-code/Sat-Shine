from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import json
from pathlib import Path
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Preserve and restore user data automatically'
    
    def add_arguments(self, parser):
        parser.add_argument('--action', type=str, choices=['backup', 'restore', 'ensure'], 
                          default='ensure', help='Action to perform')
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'backup':
            self.backup_users()
        elif action == 'restore':
            self.restore_users()
        else:
            self.ensure_users_exist()
    
    def backup_users(self):
        """Backup all users to persistent storage"""
        try:
            backup_dir = Path('persistent_data')
            backup_dir.mkdir(exist_ok=True)
            
            users_data = []
            for user in User.objects.all():
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
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully backed up {len(users_data)} users')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {e}')
            )
    
    def restore_users(self):
        """Restore users from backup"""
        try:
            backup_file = Path('persistent_data/users_persistent.json')
            if not backup_file.exists():
                self.stdout.write(
                    self.style.WARNING('No backup file found')
                )
                return
            
            with open(backup_file, 'r') as f:
                users_data = json.load(f)
            
            restored_count = 0
            for user_data in users_data:
                user, created = User.objects.get_or_create(
                    employee_id=user_data['employee_id'],
                    defaults=user_data
                )
                if created:
                    restored_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Restored {restored_count} users from backup')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restore failed: {e}')
            )
    
    def ensure_users_exist(self):
        """Ensure critical users exist, create if missing"""
        try:
            # Check if admin exists
            admin_count = User.objects.filter(role='admin').count()
            field_count = User.objects.filter(role='field_officer').count()
            
            self.stdout.write(f'Current: {admin_count} admins, {field_count} field officers')
            
            # If missing users, try restore first
            if admin_count == 0 or field_count == 0:
                self.restore_users()
                
                # Recheck after restore
                admin_count = User.objects.filter(role='admin').count()
                field_count = User.objects.filter(role='field_officer').count()
            
            # Create defaults if still missing
            if admin_count == 0:
                self.create_default_admin()
            
            if field_count == 0:
                self.create_default_field_officers()
            
            # Always backup after ensuring users exist
            self.backup_users()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ensure users failed: {e}')
            )
    
    def create_default_admin(self):
        """Create default admin user"""
        admin, created = User.objects.get_or_create(
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
            self.stdout.write(
                self.style.SUCCESS('Created default admin: MP0001')
            )
    
    def create_default_field_officers(self):
        """Create default field officers"""
        officers = [
            {'id': 'MGJ00001', 'name': 'RAJESH PATEL', 'dccb': 'AHMEDABAD', 'designation': 'MT'},
            {'id': 'MGJ00002', 'name': 'PRIYA SHAH', 'dccb': 'BARODA', 'designation': 'DC'},
            {'id': 'MGJ00003', 'name': 'AMIT DESAI', 'dccb': 'SURAT', 'designation': 'MT'},
        ]
        
        created_count = 0
        for officer in officers:
            first_name, last_name = officer['name'].split(' ', 1)
            user, created = User.objects.get_or_create(
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
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Created {created_count} default field officers')
            )