# Enhanced Django Models for Enterprise Workforce Management

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid

class Role(models.Model):
    """Role definitions with hierarchy"""
    name = models.CharField(max_length=50, unique=True)
    level = models.IntegerField()  # 1=Field Officer, 10=Super Admin
    can_approve_attendance = models.BooleanField(default=False)
    can_approve_travel = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'roles'
        indexes = [models.Index(fields=['level'])]

class DCCB(models.Model):
    """District Central Cooperative Bank units"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    geofence_radius = models.IntegerField(default=200)  # meters
    
    class Meta:
        db_table = 'dccb'

class CustomUser(AbstractUser):
    """Enhanced user model with enterprise fields"""
    employee_id = models.CharField(
        max_length=10, 
        unique=True,
        validators=[RegexValidator(r'^(MGJ\d{5}|MP\d{4})$')]
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    designation = models.CharField(max_length=50)
    dccb = models.ForeignKey(DCCB, on_delete=models.PROTECT)
    reporting_manager = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    contact = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'employees'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['role', 'dccb']),
            models.Index(fields=['reporting_manager'])
        ]

class Attendance(models.Model):
    """Daily attendance with geo-location"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'), 
        ('half_day', 'Half Day')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    check_in_time = models.TimeField(null=True)
    check_out_time = models.TimeField(null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    location_accuracy = models.FloatField(null=True)
    workplace = models.CharField(max_length=100, null=True)
    travel_approved = models.BooleanField(default=False)
    dc_confirmed = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['date', 'employee']),
            models.Index(fields=['status', 'dc_confirmed']),
            models.Index(fields=['admin_approved'])
        ]

class TravelRequest(models.Model):
    """Travel approval workflow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    er_id = models.CharField(max_length=17)
    distance_km = models.IntegerField()
    purpose = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL, related_name='approved_travels')
    remarks = models.TextField(null=True)
    
    class Meta:
        db_table = 'travel_requests'
        indexes = [models.Index(fields=['status', 'from_date'])]

class AuditLog(models.Model):
    """Immutable audit trail"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actor = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    action_type = models.CharField(max_length=50)
    target_table = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor', 'action_type'])
        ]