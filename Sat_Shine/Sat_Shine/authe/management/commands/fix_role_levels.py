# Data migration to fix role levels

from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Fix role levels for existing users'
    
    def handle(self, *args, **options):
        # Update admin users
        admin_count = CustomUser.objects.filter(role='admin').update(
            role_level=10,
            can_approve_attendance=True,
            can_approve_travel=True
        )
        
        # Update field officers
        field_count = CustomUser.objects.filter(role='field_officer').update(
            role_level=1,
            can_approve_attendance=False,
            can_approve_travel=False
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {admin_count} admin users and {field_count} field officers'
            )
        )