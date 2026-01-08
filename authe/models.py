from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import re

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('field_officer', 'Field Officer'),
        ('admin', 'Admin'),
    ]
    
    DESIGNATION_CHOICES = [
        ('MT', 'MT'),
        ('DC', 'DC'),
        ('Support', 'Support'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
        ('Delivery Head', 'Delivery Head'),
    ]
    
    DCCB_CHOICES = [
        ('AHMEDABAD', 'AHMEDABAD'),
        ('BANASKANTHA', 'BANASKANTHA'),
        ('BARODA', 'BARODA'),
        ('MAHESANA', 'MAHESANA'),
        ('SABARKANTHA', 'SABARKANTHA'),
        ('BHARUCH', 'BHARUCH'),
        ('KHEDA', 'KHEDA'),
        ('PANCHMAHAL', 'PANCHMAHAL'),
        ('SURENDRANAGAR', 'SURENDRANAGAR'),
        ('JAMNAGAR', 'JAMNAGAR'),
        ('JUNAGADH', 'JUNAGADH'),
        ('KODINAR', 'KODINAR'),
        ('KUTCH', 'KUTCH'),
        ('VALSAD', 'VALSAD'),
        ('AMRELI', 'AMRELI'),
        ('BHAVNAGAR', 'BHAVNAGAR'),
        ('RAJKOT', 'RAJKOT'),
        ('SURAT', 'SURAT'),
    ]
    
    employee_id = models.CharField(
        max_length=8, 
        unique=True,
        validators=[RegexValidator(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', 'Invalid Employee ID format')]
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    contact_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'Contact number must be 10 digits')]
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES)
    dccb = models.CharField(max_length=20, choices=DCCB_CHOICES, blank=True, null=True)
    reporting_manager = models.CharField(max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    def save(self, *args, **kwargs):
        # Auto-normalize Employee ID
        if self.employee_id:
            self.employee_id = self.employee_id.upper().strip()
            
        # Auto-assign role based on employee_id
        if self.employee_id.startswith('MGJ'):
            self.role = 'field_officer'
        elif self.employee_id.startswith('MP'):
            self.role = 'admin'
        
        # Convert names and reporting manager to uppercase
        if self.first_name:
            self.first_name = self.first_name.upper()
        if self.last_name:
            self.last_name = self.last_name.upper()
        if self.reporting_manager:
            self.reporting_manager = self.reporting_manager.upper()
        
        # Set username to employee_id
        self.username = self.employee_id
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.action} - {self.timestamp}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('half_day', 'Half Day'),
        ('absent', 'Absent'),
        ('auto_not_marked', 'Auto Not Marked'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    # GPS Location fields
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True)
    location_address = models.CharField(max_length=300, null=True, blank=True)
    is_location_valid = models.BooleanField(default=False)
    distance_from_office = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    @property
    def timing_status(self):
        if self.check_in_time and self.check_in_time <= time(9, 30):
            return 'On Time'
        elif self.check_in_time:
            return 'Late Arrival'
        return 'Not Marked'
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.date} - {self.status}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LEAVE_TYPES = [
        ('planned', 'Planned'),
        ('unplanned', 'Unplanned'),
    ]
    
    DURATION_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='full_day')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.leave_type} - {self.start_date} to {self.end_date}"
    
    @property
    def days_count(self):
        return float(self.days_requested)

class Holiday(models.Model):
    """Holiday model for managing company holidays"""
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f"{self.name} - {self.date}"