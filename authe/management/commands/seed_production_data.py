from django.core.management.base import BaseCommand
from authe.models import CustomUser, TravelRequest, Attendance
from django.db import transaction
from datetime import date, timedelta, time
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed production database with initial test data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding production database...")
        
        # Check if data already exists
        if CustomUser.objects.filter(designation='Associate').exists():
            self.stdout.write(self.style.WARNING('Data already exists. Skipping seeding.'))
            return
        
        try:
            with transaction.atomic():
                # Create Associate
                associate = CustomUser(
                    employee_id='MGJ00001',
                    first_name='PRODUCTION',
                    last_name='ASSOCIATE',
                    email='associate@satshine.com',
                    contact_number='9000000001',
                    designation='Associate',
                    department='Field Support',
                    multiple_dccb=['AHMEDABAD', 'SURAT', 'RAJKOT'],
                    can_approve_travel=True,
                    role='field_officer',
                    role_level=5
                )
                associate.set_password('Prod@Associate123')
                associate.save()
                self.stdout.write(f"Created Associate: {associate.employee_id}")
                
                # Create Field Officers
                officers = [
                    {'id': 'MGJ00002', 'name': 'FIELD OFFICER', 'last': 'ONE', 'designation': 'MT', 'dccb': 'AHMEDABAD'},
                    {'id': 'MGJ00003', 'name': 'FIELD OFFICER', 'last': 'TWO', 'designation': 'DC', 'dccb': 'SURAT'},
                    {'id': 'MGJ00004', 'name': 'FIELD OFFICER', 'last': 'THREE', 'designation': 'Support', 'dccb': 'RAJKOT'},
                ]
                
                for officer_data in officers:
                    officer = CustomUser(
                        employee_id=officer_data['id'],
                        first_name=officer_data['name'],
                        last_name=officer_data['last'],
                        email=f"{officer_data['id'].lower()}@satshine.com",
                        contact_number=f"900000{officer_data['id'][-3:]}",
                        designation=officer_data['designation'],
                        department='Field Support',
                        dccb=officer_data['dccb'],
                        reporting_manager='PRODUCTION MANAGER',
                        role='field_officer',
                        role_level=1
                    )
                    officer.set_password('Prod@Field123')
                    officer.save()
                    self.stdout.write(f"Created {officer_data['designation']}: {officer.employee_id}")
                
                # Create sample travel requests
                for i, officer in enumerate(CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'])):
                    travel_date = date.today() + timedelta(days=i+1)
                    TravelRequest.objects.create(
                        user=officer,
                        from_date=travel_date,
                        to_date=travel_date,
                        duration='full_day',
                        days_count=1,
                        er_id=f'ER{str(i+1).zfill(17)}',
                        distance_km=50 + (i * 10),
                        address=f'Production Test Address {i+1} for Travel Request Testing Purpose',
                        contact_person=f'900000{i:04d}',
                        purpose=f'Production travel request {i+1} for system testing and validation',
                        status='pending'
                    )
                    self.stdout.write(f"Created travel request for {officer.employee_id}")
                
                # Create sample attendance records with GPS for last 3 days
                gps_coordinates = [
                    (23.0225, 72.5714),  # Ahmedabad
                    (21.1702, 72.8311),  # Surat
                    (22.3039, 70.8022),  # Rajkot
                ]
                
                all_users = list(CustomUser.objects.filter(designation__in=['Associate', 'MT', 'DC', 'Support']))
                for day_offset in range(3):
                    attendance_date = date.today() - timedelta(days=day_offset)
                    
                    for idx, user in enumerate(all_users):
                        lat, lng = gps_coordinates[idx % len(gps_coordinates)]
                        # Add slight variation to coordinates
                        lat += (idx * 0.001) + (day_offset * 0.0005)
                        lng += (idx * 0.001) + (day_offset * 0.0005)
                        
                        Attendance.objects.create(
                            user=user,
                            date=attendance_date,
                            status='present',
                            latitude=lat,
                            longitude=lng,
                            check_in_time=time(9, 0 + (idx * 5)),  # Staggered check-in times
                            location_address=f'Test Location {idx+1}',
                            location_accuracy=10.0,
                            marked_at=timezone.now()
                        )
                
                self.stdout.write(f"Created attendance records with GPS for {len(all_users)} users (last 3 days)")
                
                self.stdout.write(self.style.SUCCESS('\nProduction database seeded successfully!'))
                self.stdout.write('\nTest Credentials:')
                self.stdout.write('   Associate: MGJ00001 / Prod@Associate123')
                self.stdout.write('   Field Officers: MGJ00002, MGJ00003, MGJ00004 / Prod@Field123')
                self.stdout.write('   Admin: MP0001 / (set via environment)')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding database: {str(e)}'))
            raise