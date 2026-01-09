@echo off
echo Testing SAT-SHINE deployment configuration...

echo.
echo 1. Running migrations...
python manage.py migrate

echo.
echo 2. Collecting static files...
python manage.py collectstatic --noinput

echo.
echo 3. Testing Gunicorn server...
echo Starting server on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
gunicorn Sat_Shine.wsgi --bind 127.0.0.1:8000 --log-level info --access-logfile - --error-logfile -