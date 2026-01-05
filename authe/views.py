from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import SignUpForm, LoginForm
from .models import CustomUser, AuditLog
import re
import json
import time

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

@require_http_methods(["GET"])
def validate_employee_id(request):
    """AJAX endpoint for Employee ID validation"""
    employee_id = request.GET.get('employee_id', '').upper().strip()
    
    # Validate patterns
    if re.match(r'^MGJ[0-9]{5}$', employee_id):
        role = 'field_officer'
        designations = [('MT', 'MT'), ('DC', 'DC'), ('Support', 'Support')]
    elif re.match(r'^MP[0-9]{4}$', employee_id):
        role = 'admin'
        designations = [('Manager', 'Manager'), ('HR', 'HR'), ('Delivery Head', 'Delivery Head')]
    else:
        return JsonResponse({'valid': False, 'error': 'Invalid Employee ID format'})
    
    # Check uniqueness
    if CustomUser.objects.filter(employee_id=employee_id).exists():
        return JsonResponse({'valid': False, 'error': 'Employee ID already exists'})
    
    return JsonResponse({
        'valid': True,
        'role': role,
        'designations': designations
    })

@require_http_methods(["GET"])
def validate_contact(request):
    """AJAX endpoint for Contact Number validation"""
    contact = request.GET.get('contact', '').strip()
    
    # Validate format
    if not re.match(r'^\d{10}$', contact):
        return JsonResponse({'valid': False, 'error': 'Must be exactly 10 digits'})
    
    # Check uniqueness
    if CustomUser.objects.filter(contact_number=contact).exists():
        return JsonResponse({'valid': False, 'error': 'Contact number already exists'})
    
    return JsonResponse({'valid': True})

@require_http_methods(["GET"])
def validate_email(request):
    """AJAX endpoint for Email validation"""
    email = request.GET.get('email', '').strip().lower()
    
    # Validate format
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return JsonResponse({'valid': False, 'error': 'Invalid email format'})
    
    # Check uniqueness
    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'valid': False, 'error': 'Email already exists'})
    
    return JsonResponse({'valid': True})

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                create_audit_log(
                    user, 
                    'User Registration', 
                    request, 
                    f'Role: {user.role}, Designation: {user.designation}'
                )
                messages.success(request, 'Profile created successfully')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            # Show specific form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'authe/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            password = form.cleaned_data['password']
            
            # Authenticate user
            user = authenticate(request, username=employee_id, password=password)
            if user and user.is_active:
                login(request, user)
                # Initialize session activity tracking
                request.session['last_activity'] = time.time()
                create_audit_log(user, 'User Login', request, f'Role: {user.role}')
                
                # Role-based redirect
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('field_dashboard')
            elif user and not user.is_active:
                messages.error(request, 'Your ID has been deactivated. Please contact Admin.')
            else:
                messages.error(request, 'Invalid employee ID or password.')
                # Log failed attempt
                try:
                    failed_user = CustomUser.objects.get(employee_id=employee_id)
                    create_audit_log(failed_user, 'Failed Login Attempt', request, 'Invalid password')
                except CustomUser.DoesNotExist:
                    pass
        else:
            messages.error(request, 'Invalid employee ID or password.')
    else:
        form = LoginForm()
    
    return render(request, 'authe/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    if request.user.is_authenticated:
        create_audit_log(request.user, 'User Logout', request)
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on role"""
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        return redirect('field_dashboard')