# AWS SSO Integration for SAT-SHINE
# Install required packages: pip install python-saml django-saml2-auth

# settings.py additions
AWS_SSO_CONFIG = {
    'SAML_SETTINGS': {
        'sp': {
            'entityId': 'https://your-domain.com/saml/metadata/',
            'assertionConsumerService': {
                'url': 'https://your-domain.com/saml/acs/',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
            },
            'singleLogoutService': {
                'url': 'https://your-domain.com/saml/sls/',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            },
            'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
            'x509cert': '',
            'privateKey': ''
        },
        'idp': {
            'entityId': 'https://portal.sso.us-east-1.amazonaws.com/saml/assertion/YOUR_SSO_INSTANCE_ID',
            'singleSignOnService': {
                'url': 'https://portal.sso.us-east-1.amazonaws.com/saml/assertion/YOUR_SSO_INSTANCE_ID',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            },
            'singleLogoutService': {
                'url': 'https://portal.sso.us-east-1.amazonaws.com/saml/logout/YOUR_SSO_INSTANCE_ID',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            },
            'x509cert': 'YOUR_AWS_SSO_CERTIFICATE'
        }
    },
    'ATTRIBUTE_MAPPING': {
        'email': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress',
        'username': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name',
        'first_name': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname',
        'last_name': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname',
        'employee_id': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/employeeid'
    }
}

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'django_saml2_auth',
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    # ... existing middleware
    'django_saml2_auth.middleware.SamlSessionMiddleware',
]

# SAML2 Auth settings
SAML2_AUTH = {
    'METADATA_AUTO_CONF_URL': 'https://portal.sso.us-east-1.amazonaws.com/saml/metadata/YOUR_SSO_INSTANCE_ID',
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
    }
}