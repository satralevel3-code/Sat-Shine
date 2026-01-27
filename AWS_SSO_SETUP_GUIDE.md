# AWS SSO Integration Setup Guide for SAT-SHINE

## 🔐 AWS SSO Configuration Steps

### 1. **Install Required Dependencies**
```bash
pip install python-saml django-saml2-auth xmlsec1
```

### 2. **AWS SSO Console Setup**

#### A. Create Application in AWS SSO
1. Go to AWS SSO Console
2. Click "Applications" → "Add a new application"
3. Choose "Add a custom SAML 2.0 application"
4. Application name: "SAT-SHINE Attendance System"

#### B. Configure Application URLs
- **Application ACS URL**: `https://your-domain.com/saml/acs/`
- **Application SAML audience**: `https://your-domain.com/saml/metadata/`
- **Start URL**: `https://your-domain.com/auth/dashboard/`
- **Relay State**: (leave empty)

#### C. Attribute Mappings
```
Subject: ${user:email}
email: ${user:email}
employeeid: ${user:employeeid}
givenname: ${user:givenname}
surname: ${user:surname}
```

### 3. **Django Settings Configuration**

Add to `settings.py`:
```python
# AWS SSO Settings
INSTALLED_APPS = [
    # ... existing apps
    'django_saml2_auth',
]

MIDDLEWARE = [
    # ... existing middleware
    'django_saml2_auth.middleware.SamlSessionMiddleware',
]

# SAML2 Configuration
SAML2_AUTH = {
    'METADATA_AUTO_CONF_URL': 'https://portal.sso.YOUR_REGION.amazonaws.com/saml/metadata/YOUR_SSO_INSTANCE_ID',
    'DEFAULT_NEXT_URL': '/auth/dashboard/',
    'CREATE_USER': True,
    'NEW_USER_PROFILE': {
        'USER_GROUPS': [],
        'ACTIVE_STATUS': True,
        'STAFF_STATUS': False,
        'SUPERUSER_STATUS': False,
    },
    'ATTRIBUTES_MAP': {
        'email': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress',
        'username': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name',
        'first_name': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname',
        'last_name': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname',
    },
    'TRIGGER': {
        'CREATE_USER': 'authe.aws_sso_views.create_sso_user',
        'BEFORE_LOGIN': 'authe.aws_sso_views.before_sso_login',
    }
}

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_saml2_auth.backends.Saml2Backend',
]
```

### 4. **URL Configuration**

Add to `authe/urls.py`:
```python
from django.urls import path, include
from . import aws_sso_views

urlpatterns = [
    # ... existing URLs
    
    # AWS SSO URLs
    path('sso/', include('django_saml2_auth.urls')),
    path('sso/login/', aws_sso_views.aws_sso_login, name='aws_sso_login'),
    path('sso/callback/', aws_sso_views.aws_sso_callback, name='aws_sso_callback'),
    path('sso/logout/', aws_sso_views.aws_sso_logout, name='aws_sso_logout'),
]
```

### 5. **Template Updates**

Update `login.html` to include SSO option:
```html
<!-- Add SSO Login Button -->
<div class="sso-login-section">
    <hr>
    <p class="text-center">Or login with</p>
    <a href="{% url 'aws_sso_login' %}" class="btn btn-primary btn-block">
        <i class="fab fa-aws"></i> Login with AWS SSO
    </a>
</div>
```

### 6. **User Provisioning**

#### A. Automatic User Creation
Users will be automatically created on first SSO login if:
- Employee ID follows MGJ/MP format
- User has valid email and attributes

#### B. Manual User Sync
```python
# Management command to sync existing users
python manage.py sync_sso_users
```

### 7. **Security Configuration**

#### A. Certificate Setup
1. Generate SSL certificates for SAML signing
2. Upload public certificate to AWS SSO
3. Configure private key in Django settings

#### B. Environment Variables
```bash
# .env file
AWS_SSO_INSTANCE_ID=your_sso_instance_id
AWS_SSO_REGION=us-east-1
SAML_CERTIFICATE_PATH=/path/to/certificate.pem
SAML_PRIVATE_KEY_PATH=/path/to/private_key.pem
```

### 8. **Testing SSO Integration**

#### A. Test Users
Create test users in AWS SSO with:
- Employee ID: MGJ00999 (for field officer)
- Employee ID: MP0999 (for admin)
- Email: test@company.com

#### B. Test Flow
1. Access: `https://your-domain.com/sso/login/`
2. Should redirect to AWS SSO login
3. Login with test credentials
4. Should redirect back to SAT-SHINE dashboard
5. User should be created/updated automatically

### 9. **Production Deployment**

#### A. DNS Configuration
- Ensure your domain has valid SSL certificate
- Configure proper DNS records

#### B. AWS SSO Production Setup
1. Configure production AWS SSO instance
2. Update application URLs to production domain
3. Set up user groups and permissions
4. Configure attribute mappings

#### C. Monitoring
- Set up CloudWatch logs for SSO events
- Monitor authentication failures
- Track user login patterns

### 10. **Troubleshooting**

#### Common Issues:
1. **SAML Response Invalid**: Check certificate configuration
2. **User Not Created**: Verify attribute mappings
3. **Redirect Loop**: Check DEFAULT_NEXT_URL setting
4. **Permission Denied**: Verify user groups in AWS SSO

#### Debug Commands:
```bash
# Check SAML configuration
python manage.py check_saml_config

# Test user creation
python manage.py test_sso_user_creation

# View SAML metadata
curl https://your-domain.com/saml/metadata/
```

### 11. **Benefits of AWS SSO Integration**

✅ **Single Sign-On**: Users login once for all applications
✅ **Centralized User Management**: Manage users in AWS SSO
✅ **Enhanced Security**: MFA and conditional access
✅ **Audit Logging**: Complete audit trail in CloudTrail
✅ **Automatic Provisioning**: Users created automatically
✅ **Role-Based Access**: Map AWS SSO groups to Django roles

### 12. **Migration Strategy**

#### Phase 1: Parallel Authentication
- Keep existing login system
- Add SSO as optional login method
- Test with pilot users

#### Phase 2: Full Migration
- Migrate all users to SSO
- Disable local authentication
- Update all login links to SSO

This setup provides enterprise-grade authentication with AWS SSO integration for the SAT-SHINE system.