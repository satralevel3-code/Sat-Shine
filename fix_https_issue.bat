@echo off
echo 🔧 Fixing HSTS/HTTPS Browser Cache Issue

echo.
echo ✅ Django settings updated to disable SSL for local development
echo.
echo 🌐 To fix your browser HSTS cache:
echo.
echo === OPTION 1: Clear Edge HSTS Cache ===
echo 1. Open Edge
echo 2. Go to: edge://net-internals/#hsts
echo 3. In "Delete domain security policies" section
echo 4. Enter: 127.0.0.1
echo 5. Click "Delete"
echo 6. Enter: localhost  
echo 7. Click "Delete"
echo.
echo === OPTION 2: Use Different Port ===
echo Instead of :8000, use :8001
echo python manage.py runserver 8001
echo Then visit: http://127.0.0.1:8001
echo.
echo === OPTION 3: Use Different Browser ===
echo Try Chrome Incognito or Firefox Private mode
echo.
echo 🚀 Starting Django server on port 8001...
echo Visit: http://127.0.0.1:8001
echo.

cd /d "C:\Users\admin\Git_demo\Sat_shine"
python manage.py runserver 8001