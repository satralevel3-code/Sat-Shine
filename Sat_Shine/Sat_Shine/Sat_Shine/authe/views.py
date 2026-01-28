from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import EnhancedSignUpForm, LoginForm
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
        designations = [('MT', 'MT'), ('DC', 'DC'), ('Support', 'Support'), ('Associate', 'Associate')]
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
    """Simplified admin-only user registration"""
    # Authentication check
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Role level check
    if request.user.role_level < 10:
        return redirect('field_dashboard')
    
    success_message = None
    
    if request.method == 'POST':
        form = EnhancedSignUpForm(request.POST)
        if form.is_valid():
            # Save user
            user = form.save()
            
            # Create audit log
            create_audit_log(
                request.user, 
                'User Created', 
                request, 
                f'Created user: {user.employee_id}, Role: {user.role}, By: {request.user.employee_id}'
            )
            
            # Show success message and reset form
            success_message = f'Employee {user.employee_id} ({user.first_name} {user.last_name}) created successfully!'
            form = EnhancedSignUpForm()  # Reset form
    else:
        form = EnhancedSignUpForm()
    
    return render(request, 'authe/register.html', {'form': form, 'success_message': success_message})

def login_view(request):
    """User login view with enhanced error handling"""
    # Force fresh CSRF token
    from django.middleware.csrf import get_token
    get_token(request)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            password = form.cleaned_data['password']
            
            # Check if user exists first
            try:
                user_exists = CustomUser.objects.get(employee_id=employee_id)
                if not user_exists.is_active:
                    messages.error(request, 'Your account is inactive. Contact administrator.')
                    return render(request, 'authe/login.html', {'form': form})
            except CustomUser.DoesNotExist:
                messages.error(request, 'Employee ID not found. Please register or contact admin.')
                return render(request, 'authe/login.html', {'form': form})
            
            # Authenticate user
            user = authenticate(request, username=employee_id, password=password)
            if user and user.is_active:
                login(request, user)
                # Initialize session activity tracking
                request.session['last_activity'] = time.time()
                create_audit_log(user, 'User Login', request, f'Role: {user.role}')
                
                # Enhanced role-based redirect
                if user.role == 'super_admin':
                    return redirect('super_admin_dashboard')
                elif user.role in ['admin', 'hr', 'manager', 'delivery_head']:
                    return redirect('admin_dashboard')
                elif user.designation == 'Associate':
                    return redirect('associate_dashboard')
                else:
                    return redirect('field_dashboard')
            else:
                messages.error(request, 'Incorrect password. Please try again.')
                # Log failed attempt
                create_audit_log(user_exists, 'Failed Login Attempt', request, 'Invalid password')
        else:
            messages.error(request, 'Please enter both Employee ID and password.')
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
    if request.user.role == 'super_admin':
        return redirect('super_admin_dashboard')
    elif request.user.role in ['admin', 'hr', 'manager', 'delivery_head']:
        return redirect('admin_dashboard')
    elif request.user.designation == 'Associate':
        return redirect('associate_dashboard')
    else:
        return redirect('field_dashboard')