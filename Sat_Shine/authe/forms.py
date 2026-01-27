from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import CustomUser
import re
import pandas as pd
from django.core.exceptions import ValidationError

class EnhancedSignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['employee_id', 'first_name', 'last_name', 'designation', 'department',
                 'contact_number', 'dccb', 'multiple_dccb', 'reporting_manager', 'email', 
                 'password1', 'password2']
    
    employee_id = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'username',
            'style': 'text-transform: uppercase;',
            'id': 'id_employee_id',
            'placeholder': 'MGJ00001 or MP0001'
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
            ('Associate', 'Associate'),
            ('Manager', 'Manager'),
            ('HR', 'HR'),
            ('Delivery Head', 'Delivery Head')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control', 
            'id': 'id_designation'
        })
    )
    department = forms.ChoiceField(
        choices=[('', 'Select Department')] + list(CustomUser.DEPARTMENT_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_department'
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
    multiple_dccb = forms.MultipleChoiceField(
        choices=CustomUser.DCCB_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
            'id': 'id_multiple_dccb'
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
        }),
        help_text='12-16 characters with uppercase, lowercase, number, and symbol'
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
            raise forms.ValidationError('Invalid Employee ID format. Use MGJ00001 or MP0001 format.')
        
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
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            # Enhanced password validation (12-16 characters)
            if len(password) < 12 or len(password) > 16:
                raise forms.ValidationError('Password must be 12-16 characters long.')
            if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).*$', password):
                raise forms.ValidationError(
                    'Password must include uppercase, lowercase, number, and symbol (!@#$%^&*).'
                )
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        employee_id = cleaned_data.get('employee_id')
        designation = cleaned_data.get('designation')
        dccb = cleaned_data.get('dccb')
        multiple_dccb = cleaned_data.get('multiple_dccb')
        reporting_manager = cleaned_data.get('reporting_manager')
        department = cleaned_data.get('department')
        
        if employee_id and designation:
            if employee_id.startswith('MGJ'):  # Field Officer
                # Validate designation for Field Officer
                if designation not in ['MT', 'DC', 'Support', 'Associate']:
                    raise forms.ValidationError('Invalid designation for Field Officer.')
                
                # DCCB validation
                if designation == 'Associate':
                    if not multiple_dccb:
                        raise forms.ValidationError('Multiple DCCB selection required for Associates.')
                    cleaned_data['dccb'] = None  # Clear single DCCB for Associates
                else:
                    if not dccb:
                        raise forms.ValidationError('DCCB is required for Field Officers.')
                    cleaned_data['multiple_dccb'] = []  # Clear multiple DCCB for non-Associates
                
                # Reporting Manager is mandatory for Field Officer
                if not reporting_manager:
                    raise forms.ValidationError('Reporting Manager is required for Field Officers.')
                    
            elif employee_id.startswith('MP'):  # Admin
                # Validate designation for Admin
                if designation not in ['Manager', 'HR', 'Delivery Head']:
                    raise forms.ValidationError('Invalid designation for Admin users.')
                # Clear DCCB fields for Admin users
                cleaned_data['dccb'] = None
                cleaned_data['multiple_dccb'] = []
                cleaned_data['reporting_manager'] = None
        
        # Department is mandatory for all users
        if not department:
            raise forms.ValidationError('Department is required for all employees.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Handle multiple DCCB for Associates
        if self.cleaned_data.get('multiple_dccb'):
            user.multiple_dccb = self.cleaned_data['multiple_dccb']
        if commit:
            user.save()
        return user

class BulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'id': 'id_excel_file'
        }),
        help_text='Upload Excel file (.xlsx) with employee data'
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if not file:
            raise forms.ValidationError('Please select an Excel file.')
        
        if not file.name.endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Please upload a valid Excel file (.xlsx or .xls).')
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB.')
        
        return file

# Keep original form for backward compatibility
SignUpForm = EnhancedSignUpForm

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