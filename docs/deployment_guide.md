# SAT-SHINE Deployment Guide

## Quick Fix for Current Error

### Step 1: Switch to SQLite Mode (Development)
```bash
# Already done - .env file updated with USE_POSTGRESQL=false
```

### Step 2: Install Missing Dependencies
```bash
cd C:\Users\admin\Git_demo\Sat_shine
pip install psycopg2-binary
```

### Step 3: Run Server
```bash
python manage.py runserver
```

## Production Deployment Options

### Option 1: Cloud Deployment (Recommended)

#### A. Heroku Deployment
```bash
# 1. Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create app
heroku create sat-shine-app

# 4. Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# 5. Set environment variables
heroku config:set DEBUG=False
heroku config:set USE_POSTGRESQL=true
heroku config:set SECRET_KEY=your-secret-key-here

# 6. Deploy
git add .
git commit -m "Production deployment"
git push heroku main

# 7. Run migrations
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

#### B. Railway Deployment
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway init
railway add postgresql
railway deploy
```

### Option 2: Local Production Setup

#### Windows PostgreSQL Setup
```bash
# 1. Download PostgreSQL 15+
# https://www.postgresql.org/download/windows/

# 2. Install PostGIS extension
# During PostgreSQL installation, select PostGIS in Stack Builder

# 3. Create database
psql -U postgres
CREATE DATABASE sat_shine_db;
CREATE USER sat_shine_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sat_shine_db TO sat_shine_user;
\q

# 4. Update .env file
USE_POSTGRESQL=true
DB_NAME=sat_shine_db
DB_USER=sat_shine_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

#### Install GDAL (Windows)
```bash
# Option 1: OSGeo4W (Recommended)
# Download from: https://trac.osgeo.org/osgeo4w/
# Install with GDAL package

# Option 2: Conda
conda install -c conda-forge gdal

# Option 3: Pip (may require Visual Studio)
pip install GDAL
```

### Option 3: Docker Deployment

#### Create Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "Sat_Shine.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_POSTGRESQL=true
      - DB_HOST=db
    depends_on:
      - db
  
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: sat_shine_db
      POSTGRES_USER: sat_shine_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Mobile App Deployment

### PWA Conversion
```bash
# 1. Add to base.html
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#1e3a8a">

# 2. Create service worker
# File: static/sw.js (already provided in README)

# 3. Generate app icons
# Use: https://www.pwabuilder.com/imageGenerator
```

### APK Generation
```bash
# Method 1: PWA Builder (Easiest)
# 1. Deploy to production URL
# 2. Visit: https://www.pwabuilder.com/
# 3. Enter your URL
# 4. Download APK

# Method 2: Capacitor
npm install -g @capacitor/cli
npx cap init "SAT-SHINE" "com.satshine.app"
npx cap add android
npx cap sync
npx cap open android
```

## Security Checklist

### Production Settings
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configured
- [ ] SECRET_KEY secured
- [ ] HTTPS enabled
- [ ] Database credentials secured
- [ ] Static files configured

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
USE_POSTGRESQL=true
DB_NAME=sat_shine_db
DB_USER=sat_shine_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Troubleshooting

### Common Issues

1. **GDAL Library Error**
   ```bash
   # Windows: Install OSGeo4W
   # Linux: sudo apt-get install gdal-bin libgdal-dev
   # Mac: brew install gdal
   ```

2. **PostgreSQL Connection Error**
   ```bash
   # Check PostgreSQL service is running
   # Verify credentials in .env file
   # Test connection: psql -h localhost -U sat_shine_user -d sat_shine_db
   ```

3. **Migration Errors**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Performance Optimization

### Database Indexing
```sql
-- Already implemented in models.py
CREATE INDEX idx_attendance_date_user ON authe_attendance(date, user_id);
CREATE INDEX idx_user_employee_id ON authe_customuser(employee_id);
```

### Static Files
```python
# settings.py
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Monitoring & Maintenance

### Log Monitoring
```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Backup Strategy
```bash
# Database backup
pg_dump -h localhost -U sat_shine_user sat_shine_db > backup.sql

# Restore
psql -h localhost -U sat_shine_user sat_shine_db < backup.sql
```

## Next Steps

1. **Immediate**: Run `python manage.py runserver` (SQLite mode)
2. **Short-term**: Deploy to Heroku/Railway for testing
3. **Long-term**: Set up production PostgreSQL + PostGIS
4. **Mobile**: Generate PWA and APK for distribution

Choose deployment method based on your requirements:
- **Development/Testing**: SQLite (current setup)
- **Small Production**: Heroku/Railway
- **Enterprise**: Self-hosted PostgreSQL + PostGIS
- **Mobile**: PWA + APK generation