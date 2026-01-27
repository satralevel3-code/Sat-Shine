# SAT-SHINE Attendance & Leave Management System

## 🌟 Overview

SAT-SHINE is a comprehensive Django-based Attendance and Leave Management System designed for field officers and administrative staff. The system provides real-time attendance tracking, geo-location verification, leave management, and advanced analytics with enterprise-grade security and user experience.

## 🚀 Key Features

### 🔐 Authentication & Role Management
- **Dual Employee ID Format**: MGJ00001 (Field Officers) / MP0001 (Admin)
- **Role-Based Access Control**: Automatic role assignment based on Employee ID
- **Session Security**: 30-minute auto-logout with activity tracking
- **Progressive Form Validation**: Real-time field validation and enabling

### 📍 Attendance Management
- **Geo-Location Tracking**: GPS coordinates capture with OpenLayers mapping
- **Real-Time Marking**: Present/Absent/Half-Day status with check-in/out times
- **Late Arrival Detection**: Automatic flagging of arrivals after 9:30 AM
- **Holiday Management**: Configurable holidays with Sunday auto-exclusion
- **Monthly Grid View**: Calendar-style attendance visualization

### 🏖️ Leave Management
- **Dual Leave Types**: Planned (future dates) / Unplanned (backdating allowed)
- **Duration Options**: Full Day / Half Day with auto-calculation
- **Approval Workflow**: Admin approval with remarks and timestamps
- **Query-Level Override**: Approved leave overrides attendance records

### 📊 Analytics & Reporting
- **Real-Time Dashboard**: KPI cards with live progress indicators
- **Interactive Charts**: DCCB-wise, punctuality, and completion analytics
- **Geo-Location Maps**: Color-coded attendance markers with filtering
- **Export Functionality**: CSV exports for attendance, DCCB summaries, and date ranges

### 🔔 Notification System
- **Real-Time Alerts**: Bell icon with badge counter in admin navbar
- **Event Triggers**: Leave requests and attendance marking notifications
- **Interactive Dropdown**: Latest 15 notifications with read/unread status
- **Auto-Polling**: 30-second refresh for live updates

### 🎨 Enterprise Design
- **SAT-SHINE Branding**: Deep Navy (#1e3a8a) with gradient accents
- **Responsive Layout**: Mobile-first design with Bootstrap integration
- **Accessibility**: WCAG AA compliance with proper contrast ratios
- **Professional UI**: Inter font family with institutional design system

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2+
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Authentication**: Custom User Model with role-based permissions
- **Timezone**: Asia/Kolkata with proper date handling

### Frontend
- **CSS Framework**: Bootstrap 5 with custom enterprise styling
- **JavaScript**: Vanilla JS with AJAX for real-time updates
- **Icons**: Font Awesome 6
- **Maps**: OpenLayers with EPSG:4326 coordinate system
- **Charts**: Chart.js for analytics visualization

### Infrastructure
- **Environment**: Python 3.8+
- **Dependencies**: psycopg2-binary, django-extensions
- **Security**: CSRF protection, SQL injection prevention
- **Performance**: Query optimization with select_related()

## 📋 Installation & Setup

### Prerequisites
```bash
Python 3.8+
PostgreSQL 12+ (for production)
Git
```

### 1. Clone Repository
```bash
git clone <repository-url>
cd Git_demo/Sat_shine
```

### 2. Virtual Environment
```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Configuration

#### Development (SQLite)
```python
# settings.py - Default configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### Production (PostgreSQL)
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sat_shine_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
# Or use the provided script
python create_superuser.py
```

### 7. Run Development Server
```bash
python manage.py runserver
```

## 🏗️ Project Structure

```
Sat_shine/
├── authe/                          # Authentication & Core App
│   ├── models.py                   # User, Attendance, Leave, Notification models
│   ├── views.py                    # Authentication views
│   ├── dashboard_views.py          # Field Officer dashboard
│   ├── admin_views.py              # Admin dashboard & APIs
│   ├── forms.py                    # SignUp & Login forms
│   ├── urls.py                     # URL routing
│   └── templates/authe/            # HTML templates
│       ├── login.html              # Login page
│       ├── register.html           # Registration page
│       ├── field_dashboard.html    # Field Officer dashboard
│       ├── admin_dashboard.html    # Admin main dashboard
│       ├── admin_attendance_daily.html  # Monthly attendance grid
│       ├── admin_attendance_geo_working.html  # Geo-location map
│       ├── admin_compact_analytics.html  # Analytics dashboard
│       └── ...                     # Other admin templates
├── main/                           # Main app
│   ├── views.py                    # Home redirect logic
│   └── templates/main/base.html    # Base template
├── Sat_Shine/                      # Project settings
│   ├── settings.py                 # Django configuration
│   ├── urls.py                     # Root URL configuration
│   └── wsgi.py                     # WSGI configuration
├── manage.py                       # Django management script
└── requirements.txt                # Python dependencies
```

## 👥 User Roles & Permissions

### Field Officers (MGJ00001 format)
- **Dashboard Access**: Personal attendance and leave management
- **Attendance Marking**: GPS-enabled check-in/out with location capture
- **Leave Application**: Submit planned/unplanned leave requests
- **History Viewing**: Personal attendance history with calendar view
- **Team Management**: DC users can view team attendance (if designation = 'DC')

### Admin Users (MP0001 format)
- **Full System Access**: All administrative functions
- **Employee Management**: CRUD operations on field officer accounts
- **Attendance Oversight**: Daily/monthly attendance monitoring
- **Leave Approval**: Approve/reject leave requests with remarks
- **Analytics Access**: Advanced reporting and data visualization
- **Export Capabilities**: CSV downloads for various reports
- **Notification Management**: Real-time alerts for system events

## 🔧 Configuration

### Employee ID Validation
```python
# Automatic role assignment based on Employee ID format
MGJ00001-MGJ99999: Field Officer (8 characters)
MP0001-MP9999: Admin (6 characters)
```

### DCCB (District Central Cooperative Bank) Options
```python
DCCB_CHOICES = [
    'AHMEDABAD', 'BANASKANTHA', 'BARODA', 'MAHESANA',
    'SABARKANTHA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL',
    'SURENDRANAGAR', 'JAMNAGAR', 'JUNAGADH', 'KODINAR',
    'KUTCH', 'VALSAD', 'AMRELI', 'BHAVNAGAR', 'RAJKOT', 'SURAT'
]
```

### Designation Hierarchy
```python
DESIGNATION_CHOICES = [
    'MT',           # Management Trainee
    'DC',           # District Coordinator (Team Lead)
    'Support',      # Support Staff
    'Manager',      # Manager
    'HR',           # Human Resources
    'Delivery Head' # Delivery Head
]
```

## 📊 API Endpoints

### Authentication APIs
- `POST /register/` - User registration
- `POST /login/` - User login
- `POST /logout/` - User logout
- `GET /validate-employee-id/` - Employee ID validation
- `GET /validate-contact/` - Contact number validation

### Field Officer APIs
- `POST /mark-attendance/` - Mark daily attendance
- `GET /attendance-history/` - Personal attendance history
- `GET /attendance/summary/` - Attendance summary data
- `POST /apply-leave/` - Submit leave request
- `GET /team-attendance/` - Team attendance (DC only)

### Admin APIs
- `GET /admin/employees/` - Employee list with filters
- `GET /admin/employees/<id>/` - Employee detail view
- `PUT /admin/employees/<id>/update/` - Update employee
- `PATCH /admin/employees/<id>/deactivate/` - Deactivate employee
- `GET /admin/attendance/daily/` - Daily attendance grid
- `GET /admin/attendance/geo-data/` - Geo-location data
- `GET /admin/leaves/` - Leave requests management
- `POST /admin/leaves/<id>/decide/` - Approve/reject leave
- `GET /admin/notifications/` - Notification API
- `POST /admin/notifications/<id>/read/` - Mark notification read
- `POST /admin/notifications/mark-all-read/` - Mark all notifications read

### Export APIs
- `GET /admin/export/employees/` - Export employee list
- `GET /admin/export/monthly-attendance/` - Export monthly attendance
- `GET /admin/export/dccb-summary/` - Export DCCB summary
- `GET /admin/export/date-range-attendance/` - Export date range data

## 🔒 Security Features

### Data Protection
- **CSRF Protection**: All forms protected against cross-site request forgery
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **XSS Protection**: Template auto-escaping and input sanitization
- **Session Security**: Secure session management with timeout

### Access Control
- **Role-Based Permissions**: Decorator-based access control
- **Employee ID Validation**: Regex-based format enforcement
- **Audit Logging**: All admin actions logged with IP addresses
- **Data Integrity**: Transaction-based operations for consistency

## 📱 Mobile Responsiveness

### Responsive Design
- **Mobile-First Approach**: Optimized for smartphones and tablets
- **Touch-Friendly Interface**: Large buttons and touch targets
- **Adaptive Layouts**: Grid systems that adjust to screen size
- **Performance Optimization**: Minimal JavaScript and optimized images

### GPS Integration
- **Location Accuracy**: High-precision GPS coordinate capture
- **Offline Capability**: Graceful handling of connectivity issues
- **Battery Optimization**: Efficient location services usage

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure PostgreSQL database
- [ ] Set up static file serving (WhiteNoise/Nginx)
- [ ] Configure environment variables
- [ ] Set up SSL/HTTPS
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📱 PWA & Mobile APK Deployment

### Step 1: Convert Django App to PWA

#### 1.1 Create PWA Manifest
Create `static/manifest.json`:
```json
{
  "name": "SAT-SHINE Attendance System",
  "short_name": "SAT-SHINE",
  "description": "Attendance & Leave Management System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1e3a8a",
  "theme_color": "#1e3a8a",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/static/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

#### 1.2 Create Service Worker
Create `static/sw.js`:
```javascript
const CACHE_NAME = 'sat-shine-v1';
const urlsToCache = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
```

#### 1.3 Update Base Template
Add to `main/templates/main/base.html` in `<head>`:
```html
<link rel="manifest" href="{% static 'manifest.json' %}">
<meta name="theme-color" content="#1e3a8a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="SAT-SHINE">
<link rel="apple-touch-icon" href="{% static 'icons/icon-152x152.png' %}">

<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js')
        .then(registration => console.log('SW registered'))
        .catch(registrationError => console.log('SW registration failed'));
    });
  }
</script>
```

### Step 2: Generate App Icons

#### 2.1 Create Icons Directory
```bash
mkdir static/icons
```

#### 2.2 Generate Icons (Multiple Methods)

**Method A: Online Tools**
- Use [PWA Builder](https://www.pwabuilder.com/imageGenerator)
- Upload your logo (512x512 recommended)
- Download generated icon pack

**Method B: Manual Creation**
Create icons in these sizes:
- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

### Step 3: Deploy PWA to Production

#### 3.1 Update Django Settings
```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add WhiteNoise for static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

# PWA Settings
SECURE_SSL_REDIRECT = True  # Force HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 3.2 Collect Static Files
```bash
python manage.py collectstatic
```

#### 3.3 Deploy to Cloud Platform

**Heroku Deployment:**
```bash
# Install Heroku CLI
pip install gunicorn whitenoise
echo "web: gunicorn Sat_Shine.wsgi" > Procfile
echo "python-3.9.0" > runtime.txt

# Deploy
heroku create sat-shine-app
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
heroku run python manage.py migrate
```

**Railway Deployment:**
```bash
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && gunicorn Sat_Shine.wsgi",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Step 4: Convert PWA to Mobile APK

#### Method 1: PWA Builder (Recommended)

1. **Visit PWA Builder**
   ```
   https://www.pwabuilder.com/
   ```

2. **Enter Your PWA URL**
   ```
   https://your-domain.com
   ```

3. **Generate APK**
   - Click "Build My PWA"
   - Select "Android" platform
   - Choose "TWA (Trusted Web Activity)"
   - Download APK

#### Method 2: Capacitor (Advanced)

1. **Install Capacitor**
   ```bash
   npm install -g @capacitor/cli
   npm install @capacitor/core @capacitor/android
   ```

2. **Initialize Capacitor**
   ```bash
   npx cap init "SAT-SHINE" "com.satshine.app"
   ```

3. **Add Android Platform**
   ```bash
   npx cap add android
   ```

4. **Configure capacitor.config.ts**
   ```typescript
   import { CapacitorConfig } from '@capacitor/cli';
   
   const config: CapacitorConfig = {
     appId: 'com.satshine.app',
     appName: 'SAT-SHINE',
     webDir: 'staticfiles',
     server: {
       url: 'https://your-domain.com',
       cleartext: true
     }
   };
   
   export default config;
   ```

5. **Build APK**
   ```bash
   npx cap sync
   npx cap open android
   # In Android Studio: Build > Generate Signed Bundle/APK
   ```

#### Method 3: Cordova (Alternative)

1. **Install Cordova**
   ```bash
   npm install -g cordova
   ```

2. **Create Cordova Project**
   ```bash
   cordova create sat-shine com.satshine.app "SAT-SHINE"
   cd sat-shine
   ```

3. **Add Android Platform**
   ```bash
   cordova platform add android
   ```

4. **Configure config.xml**
   ```xml
   <content src="https://your-domain.com" />
   <allow-navigation href="https://your-domain.com/*" />
   <access origin="https://your-domain.com" />
   ```

5. **Build APK**
   ```bash
   cordova build android --release
   ```

### Step 5: APK Signing & Distribution

#### 5.1 Generate Keystore
```bash
keytool -genkey -v -keystore sat-shine.keystore -alias sat-shine -keyalg RSA -keysize 2048 -validity 10000
```

#### 5.2 Sign APK
```bash
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore sat-shine.keystore app-release-unsigned.apk sat-shine
zipalign -v 4 app-release-unsigned.apk sat-shine-signed.apk
```

#### 5.3 Distribution Options

**Internal Distribution:**
- Direct APK sharing
- Firebase App Distribution
- TestFlight (iOS)

**Public Distribution:**
- Google Play Store
- Samsung Galaxy Store
- Amazon Appstore

### Step 6: Testing & Optimization

#### 6.1 PWA Testing
```bash
# Lighthouse PWA audit
npm install -g lighthouse
lighthouse https://your-domain.com --view
```

#### 6.2 Mobile Testing
- Test on multiple devices
- Check GPS functionality
- Verify offline capabilities
- Test push notifications

### Step 7: Production Monitoring

#### 7.1 Analytics Setup
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

#### 7.2 Error Tracking
```javascript
// Sentry integration
import * as Sentry from "@sentry/browser";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
});
```

### Quick Deployment Commands

```bash
# Complete PWA deployment
python manage.py collectstatic --noinput
heroku config:set DEBUG=False
git add .
git commit -m "PWA deployment"
git push heroku main
heroku run python manage.py migrate

# Generate APK with PWA Builder
# 1. Visit https://www.pwabuilder.com/
# 2. Enter: https://your-heroku-app.herokuapp.com
# 3. Click "Build My PWA" > Android > Download APK
```

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration with both employee ID formats
- [ ] Login/logout functionality
- [ ] Attendance marking with GPS
- [ ] Leave application and approval workflow
- [ ] Admin dashboard KPIs and real-time updates
- [ ] Notification system functionality
- [ ] Export functionality
- [ ] Mobile responsiveness

### Data Validation
- [ ] Employee ID format validation
- [ ] Contact number uniqueness
- [ ] Email format and uniqueness
- [ ] Date range validations
- [ ] GPS coordinate validation

## 🤝 Contributing

### Development Guidelines
1. Follow Django best practices
2. Maintain consistent code formatting
3. Write descriptive commit messages
4. Test thoroughly before submitting
5. Update documentation for new features

### Code Style
- Use Django's coding style guidelines
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for complex functions
- Keep functions focused and modular

## 📞 Support

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
2. **Migration Errors**: Run `python manage.py makemigrations` before `migrate`
3. **Static Files**: Run `python manage.py collectstatic` for production
4. **GPS Issues**: Ensure HTTPS for location services in production

### Contact Information
- **Project Lead**: [Your Name]
- **Email**: [your.email@domain.com]
- **Documentation**: [Link to detailed docs]
- **Issue Tracker**: [Link to GitHub issues]

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django Framework for robust backend development
- Bootstrap for responsive UI components
- OpenLayers for geo-location mapping
- Chart.js for data visualization
- Font Awesome for professional icons

---

**SAT-SHINE** - Streamlined Attendance Tracking - Systematic Human Resource Intelligence & Network Enhancement