from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import BulkUploadForm
from .models import CustomUser, AuditLog
import pandas as pd
import re
import json
from django.db import transaction
from django.core.exceptions import ValidationError

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_audit_log(user, action, request, details=None):
    """Create audit log entry"""
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        details=details or ''
    )

@login_required
def bulk_upload_view(request):
    """Bulk employee upload interface"""
    if request.user.role_level < 10:
        messages.error(request, 'Only administrators can perform bulk uploads')
        return redirect('admin_employee_list')
    
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Validate and process data
                validation_results = validate_bulk_data(df)
                
                if validation_results['is_valid']:
                    # Store validated data in session for preview
                    request.session['bulk_upload_data'] = validation_results['data']
                    return redirect('bulk_upload_preview')
                else:
                    # Show validation errors
                    context = {
                        'form': form,
                        'validation_errors': validation_results['errors'],
                        'preview_data': validation_results.get('preview_data', [])
                    }
                    return render(request, 'authe/bulk_upload.html', context)
                    
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                form = BulkUploadForm()
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BulkUploadForm()
    
    return render(request, 'authe/bulk_upload.html', {'form': form})

@login_required
def bulk_upload_preview(request):
    """Preview bulk upload data before final submission"""
    if request.user.role_level < 10:
        messages.error(request, 'Access denied')
        return redirect('admin_employee_list')
    
    bulk_data = request.session.get('bulk_upload_data')
    if not bulk_data:
        messages.error(request, 'No upload data found. Please upload file again.')
        return redirect('bulk_upload')
    
    if request.method == 'POST':
        # Process bulk creation
        try:
            with transaction.atomic():
                created_count = 0
                for row_data in bulk_data:
                    user = CustomUser.objects.create_user(
                        employee_id=row_data['employee_id'],
                        email=row_data['email'],
                        password=row_data['password'],
                        first_name=row_data['first_name'],
                        last_name=row_data['last_name'],
                        designation=row_data['designation'],
                        department=row_data['department'],
                        contact_number=row_data['contact_number'],
                        dccb=row_data.get('dccb'),
                        multiple_dccb=row_data.get('multiple_dccb', []),
                        reporting_manager=row_data.get('reporting_manager')
                    )
                    created_count += 1
                
                # Clear session data
                del request.session['bulk_upload_data']
                
                # Create audit log
                create_audit_log(
                    request.user,
                    'Bulk User Creation',
                    request,
                    f'Created {created_count} employees via bulk upload'
                )
                
                messages.success(request, f'Successfully created {created_count} employee accounts')
                return redirect('admin_employee_list')
                
        except Exception as e:
            messages.error(request, f'Error creating employees: {str(e)}')
    
    return render(request, 'authe/bulk_upload_preview.html', {
        'preview_data': bulk_data,
        'total_count': len(bulk_data)
    })

def validate_bulk_data(df):
    """Validate bulk upload Excel data"""
    required_columns = [
        'Employee ID', 'First Name', 'Last Name', 'Designation', 
        'Department', 'Contact Number', 'Email ID', 'Password', 'Confirm Password'
    ]
    
    errors = []
    preview_data = []
    validated_data = []
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {
            'is_valid': False,
            'errors': [f'Missing required columns: {", ".join(missing_columns)}'],
            'data': []
        }
    
    # Validate each row
    for index, row in df.iterrows():
        row_errors = []
        row_data = {}
        
        try:
            # Employee ID validation
            employee_id = str(row['Employee ID']).upper().strip()
            if not re.match(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', employee_id):
                row_errors.append(f'Row {index+2}: Invalid Employee ID format')
            elif CustomUser.objects.filter(employee_id=employee_id).exists():
                row_errors.append(f'Row {index+2}: Employee ID already exists')
            else:
                row_data['employee_id'] = employee_id
            
            # Name validation
            first_name = str(row['First Name']).upper().strip()
            last_name = str(row['Last Name']).upper().strip()
            if not first_name or first_name == 'nan':
                row_errors.append(f'Row {index+2}: First Name is required')
            else:
                row_data['first_name'] = first_name
            
            if not last_name or last_name == 'nan':
                row_errors.append(f'Row {index+2}: Last Name is required')
            else:
                row_data['last_name'] = last_name
            
            # Designation validation
            designation = str(row['Designation']).strip()
            valid_designations = ['MT', 'DC', 'Support', 'Associate', 'Manager', 'HR', 'Delivery Head']
            if designation not in valid_designations:
                row_errors.append(f'Row {index+2}: Invalid designation')
            else:
                row_data['designation'] = designation
            
            # Department validation
            department = str(row['Department']).strip()
            valid_departments = [choice[0] for choice in CustomUser.DEPARTMENT_CHOICES]
            if department not in valid_departments:
                row_errors.append(f'Row {index+2}: Invalid department')
            else:
                row_data['department'] = department
            
            # Contact number validation
            contact = re.sub(r'[^0-9]', '', str(row['Contact Number']))
            if not re.match(r'^[0-9]{10}$', contact):
                row_errors.append(f'Row {index+2}: Invalid contact number format')
            elif CustomUser.objects.filter(contact_number=contact).exists():
                row_errors.append(f'Row {index+2}: Contact number already exists')
            else:
                row_data['contact_number'] = contact
            
            # Email validation
            email = str(row['Email ID']).lower().strip()
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                row_errors.append(f'Row {index+2}: Invalid email format')
            elif CustomUser.objects.filter(email=email).exists():
                row_errors.append(f'Row {index+2}: Email already exists')
            else:
                row_data['email'] = email
            
            # Password validation
            password = str(row['Password'])
            confirm_password = str(row['Confirm Password'])
            if len(password) < 12 or len(password) > 16:
                row_errors.append(f'Row {index+2}: Password must be 12-16 characters')
            elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).*$', password):
                row_errors.append(f'Row {index+2}: Password must include uppercase, lowercase, number, and symbol')
            elif password != confirm_password:
                row_errors.append(f'Row {index+2}: Passwords do not match')
            else:
                row_data['password'] = password
            
            # Role-specific validation
            if employee_id.startswith('MGJ'):  # Field Officer
                if designation not in ['MT', 'DC', 'Support', 'Associate']:
                    row_errors.append(f'Row {index+2}: Invalid designation for Field Officer')
                
                # DCCB validation
                if designation == 'Associate':
                    # Multiple DCCB for Associates (if provided in Excel)
                    if 'DCCB' in df.columns and pd.notna(row['DCCB']):
                        dccb_list = [d.strip() for d in str(row['DCCB']).split(',')]
                        valid_dccbs = [choice[0] for choice in CustomUser.DCCB_CHOICES]
                        invalid_dccbs = [d for d in dccb_list if d not in valid_dccbs]
                        if invalid_dccbs:
                            row_errors.append(f'Row {index+2}: Invalid DCCB(s): {", ".join(invalid_dccbs)}')
                        else:
                            row_data['multiple_dccb'] = dccb_list
                else:
                    # Single DCCB for other Field Officers
                    if 'DCCB' in df.columns and pd.notna(row['DCCB']):
                        dccb = str(row['DCCB']).strip()
                        valid_dccbs = [choice[0] for choice in CustomUser.DCCB_CHOICES]
                        if dccb not in valid_dccbs:
                            row_errors.append(f'Row {index+2}: Invalid DCCB')
                        else:
                            row_data['dccb'] = dccb
                    else:
                        row_errors.append(f'Row {index+2}: DCCB is required for Field Officers')
                
                # Reporting Manager validation
                if 'Reporting Manager' in df.columns and pd.notna(row['Reporting Manager']):
                    row_data['reporting_manager'] = str(row['Reporting Manager']).upper().strip()
                else:
                    row_errors.append(f'Row {index+2}: Reporting Manager is required for Field Officers')
            
            elif employee_id.startswith('MP'):  # Admin
                if designation not in ['Manager', 'HR', 'Delivery Head']:
                    row_errors.append(f'Row {index+2}: Invalid designation for Admin user')
            
            # Add to preview data
            preview_row = {
                'row_number': index + 2,
                'employee_id': employee_id,
                'name': f"{first_name} {last_name}",
                'designation': designation,
                'department': department,
                'contact': contact,
                'email': email,
                'errors': row_errors
            }
            preview_data.append(preview_row)
            
            if not row_errors:
                validated_data.append(row_data)
            else:
                errors.extend(row_errors)
        
        except Exception as e:
            error_msg = f'Row {index+2}: Error processing data - {str(e)}'
            errors.append(error_msg)
            preview_data.append({
                'row_number': index + 2,
                'employee_id': 'Error',
                'name': 'Error',
                'designation': 'Error',
                'department': 'Error',
                'contact': 'Error',
                'email': 'Error',
                'errors': [error_msg]
            })
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'data': validated_data,
        'preview_data': preview_data
    }

@login_required
def download_template(request):
    """Download Excel template for bulk upload"""
    if request.user.role_level < 10:
        messages.error(request, 'Access denied')
        return redirect('admin_employee_list')
    
    # Create sample Excel template
    template_data = {
        'Employee ID': ['MGJ00001', 'MP0001'],
        'First Name': ['JOHN', 'JANE'],
        'Last Name': ['DOE', 'SMITH'],
        'Designation': ['MT', 'Manager'],
        'Department': ['Field Support', 'HR'],
        'Contact Number': ['9876543210', '9876543211'],
        'DCCB': ['AHMEDABAD', ''],
        'Reporting Manager': ['MANAGER NAME', ''],
        'Email ID': ['john.doe@example.com', 'jane.smith@example.com'],
        'Password': ['SecurePass123!', 'SecurePass456@'],
        'Confirm Password': ['SecurePass123!', 'SecurePass456@']
    }
    
    df = pd.DataFrame(template_data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="employee_bulk_upload_template.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Data')
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            'Field': ['Employee ID', 'First Name', 'Last Name', 'Designation', 'Department', 
                     'Contact Number', 'DCCB', 'Reporting Manager', 'Email ID', 'Password'],
            'Format': ['MGJ00001 or MP0001', 'UPPERCASE TEXT', 'UPPERCASE TEXT', 
                      'MT/DC/Support/Associate/Manager/HR/Delivery Head',
                      'HR/SPMU/Central Tech Support/CCR/Field Support/IT Admin',
                      '10 digits', 'Required for Field Officers', 'Required for Field Officers',
                      'valid@email.com', '12-16 chars with upper/lower/number/symbol'],
            'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Conditional', 'Conditional', 'Yes', 'Yes']
        })
        instructions.to_excel(writer, index=False, sheet_name='Instructions')
    
    return response