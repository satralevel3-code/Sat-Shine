from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import re
import json

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
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    date_of_joining = models.DateField(null=True, blank=True)
    registration_at = models.DateTimeField(auto_now_add=True)
    
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
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active_employee(self):
        return self.status == 'active'

class AuditLog(models.Model):
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_actions')
    action = models.CharField(max_length=100)
    target_table = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50)
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin', 'timestamp']),
            models.Index(fields=['target_table', 'target_id']),
        ]
    
    def __str__(self):
        return f"{self.admin.employee_id} - {self.action} - {self.timestamp}"

class Holiday(models.Model):
    date = models.DateField()
    name = models.CharField(max_length=100)
    dccb = models.CharField(max_length=20, choices=CustomUser.DCCB_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date', 'dccb']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['dccb']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.date}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('H', 'Half Day'),
        ('A', 'Absent'),
        ('NM', 'Not Marked'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    code = models.CharField(max_length=2, choices=STATUS_CHOICES)
    marked_at = models.DateTimeField(null=True, blank=True)
    marked_by = models.CharField(max_length=8, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    reverse_geocode_address = models.TextField(null=True, blank=True)
    late_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.date} - {self.code}"
    
    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES)[self.code]

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
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    comments = models.TextField(null=True, blank=True)
    decided_by_admin = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_leaves')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['from_date', 'to_date']),
        ]
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.type} - {self.from_date} to {self.to_date}"