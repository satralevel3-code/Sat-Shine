# HR Data Backfill Script - Production Safe

from django.core.management.base import BaseCommand
from authe.models import CustomUser
from datetime import date

class Command(BaseCommand):
    help = 'Backfill date_of_joining for existing users with proper HR data'
    
    def handle(self, *args, **options):
        # Backfill with reasonable default for existing users
        # In production, this should be actual HR data from Excel/CSV
        
        updated_count = CustomUser.objects.filter(
            date_of_joining__isnull=True
        ).update(
            date_of_joining=date(2024, 1, 1)  # Default for existing users
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully backfilled date_of_joining for {updated_count} users'
            )
        )
        
        # Show users that need proper HR data
        users_needing_doj = CustomUser.objects.filter(
            date_of_joining=date(2024, 1, 1)
        ).values_list('employee_id', 'first_name', 'last_name')
        
        if users_needing_doj:
            self.stdout.write(
                self.style.WARNING(
                    f'\\nUsers with default DOJ (need HR update):'
                )
            )
            for emp_id, first_name, last_name in users_needing_doj:
                self.stdout.write(f'  {emp_id} - {first_name} {last_name}')
                
        self.stdout.write(
            self.style.SUCCESS(
                '\\nRecommendation: Update with actual joining dates via Admin or Excel upload'
            )
        )