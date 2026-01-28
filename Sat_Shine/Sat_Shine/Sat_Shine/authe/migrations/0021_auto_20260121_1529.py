from django.db import migrations

def set_default_values(apps, schema_editor):
    # Skip - fields don't exist yet
    pass

def reverse_default_values(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('authe', '0020_systemauditlog_travelrequest_delete_holiday_and_more'),
    ]

    operations = [
        migrations.RunPython(set_default_values, reverse_default_values),
    ]