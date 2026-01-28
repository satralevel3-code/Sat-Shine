"""
AWS SSO Authentication Views for SAT-SHINE
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import CustomUser
import json

def aws_sso_login(request):
    """Initiate AWS SSO login"""
    # Redirect to AWS SSO login URL
    aws_sso_url = "https://portal.sso.us-east-1.amazonaws.com/saml/assertion/YOUR_SSO_INSTANCE_ID"
    return redirect(aws_sso_url)

@csrf_exempt
def aws_sso_callback(request):
    """Handle AWS SSO callback"""
    if request.method == 'POST':
        try:
            # Parse SAML response
            saml_response = request.POST.get('SAMLResponse')
            
            if not saml_response:
                messages.error(request, 'Invalid SAML response')
                return redirect('login')
            
            # Decode and validate SAML response (implement SAML validation)
            user_data = parse_saml_response(saml_response)
            
            if user_data:
                # Get or create user
                user = get_or_create_sso_user(user_data)
                
                if user:
                    login(request, user)
                    
                    # Redirect based on role
                    if user.role_level >= 10:
                        return redirect('admin_dashboard')
                    elif user.designation == 'Associate':
                        return redirect('associate_dashboard')
                    else:
                        return redirect('field_dashboard')
                else:
                    messages.error(request, 'User account not found or inactive')
                    return redirect('login')
            else:
                messages.error(request, 'Failed to process SSO login')
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f'SSO login error: {str(e)}')
            return redirect('login')
    
    return redirect('login')

def parse_saml_response(saml_response):
    """Parse SAML response and extract user data"""
    try:
        # Implement SAML response parsing
        # This is a simplified version - use proper SAML library
        import base64
        import xml.etree.ElementTree as ET
        
        decoded_response = base64.b64decode(saml_response)
        root = ET.fromstring(decoded_response)
        
        # Extract user attributes from SAML response
        user_data = {
            'email': extract_saml_attribute(root, 'emailaddress'),
            'employee_id': extract_saml_attribute(root, 'employeeid'),
            'first_name': extract_saml_attribute(root, 'givenname'),
            'last_name': extract_saml_attribute(root, 'surname'),
        }
        
        return user_data
        
    except Exception as e:
        print(f"SAML parsing error: {e}")
        return None

def extract_saml_attribute(root, attribute_name):
    """Extract specific attribute from SAML response"""
    # Implement SAML attribute extraction
    # This is a placeholder - implement proper SAML parsing
    return None

def get_or_create_sso_user(user_data):
    """Get or create user from SSO data"""
    try:
        employee_id = user_data.get('employee_id')
        email = user_data.get('email')
        
        if not employee_id:
            return None
        
        # Try to find existing user
        try:
            user = CustomUser.objects.get(employee_id=employee_id)
            
            # Update user data from SSO
            user.email = email or user.email
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
            
            return user
            
        except CustomUser.DoesNotExist:
            # Create new user if allowed
            if employee_id.startswith('MGJ') or employee_id.startswith('MP'):
                user = CustomUser.objects.create_user(
                    username=employee_id,
                    employee_id=employee_id,
                    email=email,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    is_active=True
                )
                return user
            else:
                return None
                
    except Exception as e:
        print(f"User creation error: {e}")
        return None

@login_required
def aws_sso_logout(request):
    """Handle AWS SSO logout"""
    logout(request)
    
    # Redirect to AWS SSO logout URL
    aws_sso_logout_url = "https://portal.sso.us-east-1.amazonaws.com/saml/logout/YOUR_SSO_INSTANCE_ID"
    return redirect(aws_sso_logout_url)

def sso_metadata(request):
    """Provide SAML metadata for AWS SSO configuration"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" 
                     entityID="https://your-domain.com/saml/metadata/">
    <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                   Location="https://your-domain.com/saml/acs/"
                                   index="1"/>
        <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                              Location="https://your-domain.com/saml/sls/"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""
    
    return HttpResponse(metadata_xml, content_type='application/xml')

# URL patterns for AWS SSO
"""
Add to authe/urls.py:

# AWS SSO URLs
path('sso/login/', aws_sso_login, name='aws_sso_login'),
path('sso/callback/', aws_sso_callback, name='aws_sso_callback'),
path('sso/logout/', aws_sso_logout, name='aws_sso_logout'),
path('saml/metadata/', sso_metadata, name='sso_metadata'),
path('saml/acs/', aws_sso_callback, name='saml_acs'),
path('saml/sls/', aws_sso_logout, name='saml_sls'),
"""