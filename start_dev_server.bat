@echo off
echo SAT-SHINE Development Server Startup
echo ====================================

REM Navigate to project directory
cd /d "C:\Users\admin\Git_demo\Sat_shine"

REM Activate virtual environment
echo Activating virtual environment...
call env\Scripts\activate

REM Check if PostgreSQL dependencies are installed
python -c "import psycopg2" 2>nul
if %errorlevel% neq 0 (
    echo Installing PostgreSQL dependencies...
    pip install psycopg2-binary
)

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser if it doesn't exist
echo Checking for superuser...
python -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(employee_id='MP0001').exists():
    User.objects.create_superuser(employee_id='MP0001', email='admin@satshine.com', first_name='ADMIN', last_name='USER', contact_number='9999999999', password='admin123');
    print('Superuser created: MP0001/admin123')
else:
    print('Superuser already exists')
"

REM Start development server
echo Starting development server...
echo Server will be available at: http://127.0.0.1:8000
echo Admin login: MP0001 / admin123
echo.
python manage.py runserver 127.0.0.1:8000

pause