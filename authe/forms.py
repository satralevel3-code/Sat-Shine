from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import CustomUser
import re

class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['employee_id', 'first_name', 'last_name', 'designation', 'contact_number', 
                 'dccb', 'reporting_manager', 'email', 'password1', 'password2']
    
    employee_id = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'username',
            'style': 'text-transform: uppercase;',
            'id': 'id_employee_id'
        })
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'given-name',
            'style': 'text-transform: uppercase;',
            'id': 'id_first_name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'family-name',
            'style': 'text-transform: uppercase;',
            'id': 'id_last_name'
        })
    )
    designation = forms.ChoiceField(
        choices=[
            ('', 'Select Designation'),
            ('MT', 'MT'),
            ('DC', 'DC'), 
            ('Support', 'Support'),
            ('Manager', 'Manager'),
            ('HR', 'HR'),
            ('Delivery Head', 'Delivery Head')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control', 
            'id': 'id_designation'
        })
    )
    contact_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'maxlength': '10',
            'pattern': '[0-9]{10}',
            'autocomplete': 'tel',
            'id': 'id_contact_number'
        })
    )
    dccb = forms.ChoiceField(
        choices=[('', 'Select DCCB')] + list(CustomUser.DCCB_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control', 
            'id': 'id_dccb'
        })
    )
    reporting_manager = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'text-transform: uppercase;',
            'autocomplete': 'off',
            'id': 'id_reporting_manager'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'email',
            'id': 'id_email'
        })
    )
    password1 = forms.CharField(
        label='Create Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'new-password',
            'id': 'id_password1'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'new-password',
            'id': 'id_password2'
        })
    )
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id', '').upper().strip()
        
        # Validate exact patterns: MGJ00001 (8 chars) or MP0001 (6 chars)
        if not (re.match(r'^MGJ[0-9]{5}$', employee_id) or re.match(r'^MP[0-9]{4}$', employee_id)):
            raise forms.ValidationError('Invalid Employee ID format.')
        
        # Check uniqueness
        if CustomUser.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('Employee ID already exists.')
        
        return employee_id
    
    def clean_contact_number(self):
        contact = re.sub(r'\D', '', self.cleaned_data.get('contact_number', ''))
        
        # Validate exactly 10 digits
        if not re.match(r'^\d{10}$', contact):
            raise forms.ValidationError('Contact number must be exactly 10 digits.')
        
        # Check uniqueness
        if CustomUser.objects.filter(contact_number=contact).exists():
            raise forms.ValidationError('Contact number already exists.')
        
        return contact
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not email:
            raise forms.ValidationError('Email is required.')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already exists.')
        return email
    
    def clean_reporting_manager(self):
        manager_name = self.cleaned_data.get('reporting_manager', '').upper().strip()
        return manager_name
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            # Validate password requirements
            if not re.match(r'^(?=.{8,}$)(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).*$', password):
                raise forms.ValidationError(
                    'Password must be at least 8 characters with uppercase, lowercase, digit, and special character (@$!%*?&).'
                )
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        employee_id = cleaned_data.get('employee_id')
        designation = cleaned_data.get('designation')
        dccb = cleaned_data.get('dccb')
        reporting_manager = cleaned_data.get('reporting_manager')
        
        if employee_id and designation:  # Only validate if both are present
            if employee_id.startswith('MGJ'):  # Field Officer
                # Validate designation for Field Officer
                if designation not in ['MT', 'DC', 'Support']:
                    raise forms.ValidationError('Invalid designation for Field Officer.')
                
                # DCCB is mandatory for Field Officer
                if not dccb:
                    raise forms.ValidationError('DCCB is required for Field Officers.')
                
                # Reporting Manager is mandatory for Field Officer
                if not reporting_manager:
                    raise forms.ValidationError('Reporting Manager is required for Field Officers.')
                    
            elif employee_id.startswith('MP'):  # Admin
                # Validate designation for Admin
                if designation not in ['Manager', 'HR', 'Delivery Head']:
                    raise forms.ValidationError('Invalid designation for Admin users.')
        
        return cleaned_data

class LoginForm(forms.Form):
    employee_id = forms.CharField(
        max_length=8,
        label='Employee ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'username',
            'style': 'text-transform: uppercase;',
            'id': 'id_employee_id'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'current-password',
            'id': 'id_password'
        })
    )
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id', '').upper().strip()
        return employee_id