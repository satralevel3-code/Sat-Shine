# PostgreSQL + PostGIS Setup Instructions

## Current Status
✅ **USE_POSTGRESQL=true** - Enabled in .env
❌ **GDAL Installation Failed** - Requires Visual Studio Build Tools

## Option 1: Install Visual Studio Build Tools (Recommended)

### Step 1: Download and Install Build Tools
1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "C++ build tools" workload
3. Restart computer

### Step 2: Install GDAL
```bash
pip install GDAL
```

### Step 3: Install PostgreSQL
1. Download PostgreSQL 15+: https://www.postgresql.org/download/windows/
2. During installation, use Stack Builder to install PostGIS extension

### Step 4: Setup Database
```sql
-- Run in PostgreSQL command line (psql)
CREATE DATABASE sat_shine_db;
CREATE USER sat_shine_user WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE sat_shine_db TO sat_shine_user;
\c sat_shine_db
CREATE EXTENSION postgis;
```

### Step 5: Run Migration
```bash
python migrate_to_postgis.py
python manage.py migrate
```

## Option 2: Use Conda (Alternative)

### Step 1: Install Conda
Download Miniconda: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create Environment with GDAL
```bash
conda create -n sat_shine python=3.11
conda activate sat_shine
conda install -c conda-forge gdal psycopg2 pillow
pip install django
```

### Step 3: Continue with PostgreSQL setup (same as Option 1, Steps 3-5)

## Option 3: Docker (Easiest)

### Step 1: Install Docker Desktop
Download: https://www.docker.com/products/docker-desktop/

### Step 2: Use Docker Compose
```bash
# Already provided in deployment_guide.md
docker-compose up -d
```

## Option 4: Cloud Deployment (Skip Local Setup)

### Heroku (Recommended)
```bash
heroku create sat-shine-app
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Railway
```bash
railway init
railway add postgresql
railway deploy
```

## Current Workaround: Revert to SQLite

If you want to continue development without PostgreSQL setup:

```bash
# In .env file, change:
USE_POSTGRESQL=false

# Then run:
python manage.py runserver
```

## Next Steps

Choose one option above based on your preference:
- **Option 1**: Full local setup with all features
- **Option 2**: Conda environment (easier GDAL)
- **Option 3**: Docker (containerized)
- **Option 4**: Cloud deployment (no local setup needed)

The system is designed to work in both SQLite (development) and PostgreSQL (production) modes.