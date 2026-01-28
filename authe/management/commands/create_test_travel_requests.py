from django.core.management.base import BaseCommand
from authe.models import CustomUser, TravelRequest
from django.utils import timezone
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Create test travel requests for production'

    def handle(self, *args, **options):
        self.stdout.write("Creating test travel requests...")
        
        # Get field officers
        field_officers = CustomUser.objects.filter(
            designation__in=['MT', 'DC', 'Support'], 
            is_active=True
        )
        
        if not field_officers.exists():
            self.stdout.write(self.style.ERROR('No field officers found!'))
            return
        
        # Create multiple test travel requests
        test_dates = [
            date.today() - timedelta(days=2),
            date.today() - timedelta(days=1),
            date.today(),
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=2),
        ]
        
        created_count = 0
        
        for i, officer in enumerate(field_officers[:5]):  # Create for first 5 officers
            travel_date = test_dates[i % len(test_dates)]
            
            # Check if request already exists
            existing = TravelRequest.objects.filter(
                user=officer,
                from_date=travel_date
            ).exists()
            
            if not existing:
                TravelRequest.objects.create(
                    user=officer,
                    from_date=travel_date,
                    to_date=travel_date,
                    duration='full_day',
                    days_count=1,
                    er_id=f'ER{str(i+1).zfill(17)}',
                    distance_km=25 + (i * 10),
                    address=f'Test Address {i+1} for Production Travel Request Testing Purpose Location',
                    contact_person=f'98765432{i:02d}',
                    purpose=f'Production testing travel request {i+1} for Associate dashboard verification system testing',
                    status='pending'
                )
                created_count += 1
                self.stdout.write(f"Created travel request for {officer.employee_id} on {travel_date}")
        
        total_requests = TravelRequest.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} travel requests. Total: {total_requests}'
            )
        )