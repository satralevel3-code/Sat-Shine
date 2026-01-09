@echo off
echo SAT-SHINE PostgreSQL + PostGIS Setup
echo ====================================

REM Navigate to project directory
cd /d "C:\Users\admin\Git_demo\Sat_shine"

REM Activate virtual environment
echo Activating virtual environment...
call env\Scripts\activate

REM Install PostgreSQL dependencies
echo Installing PostgreSQL dependencies...
pip install psycopg2-binary
pip install GDAL
pip install Pillow

REM Set environment variable for PostgreSQL
echo Setting PostgreSQL environment...
set USE_POSTGRESQL=true

REM Copy environment file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your PostgreSQL credentials
    pause
)

REM Run PostGIS migration
echo Running PostGIS migration...
python migrate_to_postgis.py

REM Start server with PostgreSQL
echo Starting server with PostgreSQL + PostGIS...
echo Server will be available at: http://127.0.0.1:8000
echo.
python manage.py runserver 127.0.0.1:8000

pause