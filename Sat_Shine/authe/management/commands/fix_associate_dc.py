from django.core.management.base import BaseCommand
from django.db import transaction
from authe.models import Attendance

class Command(BaseCommand):
    help = 'Fix Associate/DC attendance records - remove from DC confirmation pipeline'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("FIXING: Associate/DC Attendance Records")
        self.stdout.write("=" * 80)

        corrupted_records = Attendance.objects.filter(
            user__designation__in=['Associate', 'DC'],
            is_confirmed_by_dc=False,
            status__in=['present', 'half_day']
        )

        count = corrupted_records.count()
        self.stdout.write(f"\nFound {count} corrupted records")

        if count > 0:
            with transaction.atomic():
                updated = corrupted_records.update(
                    is_confirmed_by_dc=True,
                    confirmed_by_dc=None,
                    dc_confirmed_at=None
                )
                self.stdout.write(self.style.SUCCESS(f"\n✓ Updated {updated} records"))
                self.stdout.write(self.style.SUCCESS("✓ Associates/DCs removed from DC confirmation pipeline"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ No corrupted records found - data is clean"))

        self.stdout.write("\n" + "=" * 80)
