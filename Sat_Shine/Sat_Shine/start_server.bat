@echo off
<<<<<<< HEAD
REM Windows development server for SAT-SHINE

echo Starting SAT-SHINE Development Server...
cd Sat_shine
set DJANGO_SETTINGS_MODULE=Sat_Shine.settings.development
env\Scripts\python.exe manage.py runserver 127.0.0.1:8000
=======
echo ========================================
echo    SAT-SHINE Development Server
echo ========================================

REM Navigate to project directory
cd /d "C:\Users\admin\Git_demo\Sat_shine"

REM Check if virtual environment exists
if not exist "env\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run: python -m venv env
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🐍 Activating virtual environment...
call env\Scripts\activate.bat

REM Check Django installation
echo 🔍 Checking Django installation...
python -c "import django; print('✅ Django version:', django.get_version())" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Django not installed. Installing...
    pip install django django-extensions psycopg2-binary
)

REM Run migrations
echo 📊 Running database migrations...
python manage.py migrate

REM Start development server
echo 🚀 Starting Django development server...
echo 🌐 Access your application at: http://127.0.0.1:8000
echo 🔑 Admin panel at: http://127.0.0.1:8000/admin
echo.
python manage.py runserver 127.0.0.1:8000

pause
>>>>>>> bddc073dc40844144f1546bf65ec3173df6783fe
