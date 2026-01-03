@echo off
echo Installing missing PostgreSQL dependencies...

REM Activate virtual environment
cd /d "C:\Users\admin\Git_demo\Sat_shine"
call env\Scripts\activate

REM Install PostgreSQL dependencies
pip install psycopg2-binary
pip install psycopg2

REM Install additional dependencies if missing
pip install django-extensions
pip install pillow

echo Dependencies installed successfully!
echo.
echo Starting development server with SQLite...
python manage.py runserver 127.0.0.1:8000

pause