# Generated manually to fix reporting_manager field

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('authe', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='reporting_manager',
        ),
        migrations.AddField(
            model_name='customuser',
            name='reporting_manager',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='employee_id',
            field=models.CharField(max_length=8, unique=True, validators=[django.core.validators.RegexValidator('^(MGJ[0-9]{5}|MP[0-9]{4})$', 'Invalid Employee ID format')]),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('field_officer', 'Field Officer'), ('admin', 'Admin')], max_length=15),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='designation',
            field=models.CharField(choices=[('MT', 'MT'), ('DC', 'DC'), ('Support', 'Support'), ('Manager', 'Manager'), ('HR', 'HR'), ('Delivery Head', 'Delivery Head')], max_length=20),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='contact_number',
            field=models.CharField(max_length=10, unique=True, validators=[django.core.validators.RegexValidator('^\\d{10}$', 'Contact number must be 10 digits')]),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='details',
            field=models.TextField(blank=True, null=True),
        ),
    ]