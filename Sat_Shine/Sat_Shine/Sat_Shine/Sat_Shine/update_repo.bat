@echo off
echo Cleaning and updating GitHub repository...

echo.
echo 1. Removing cached files...
git rm -r --cached .
git add .gitignore

echo.
echo 2. Removing unnecessary files...
if exist "env\" rmdir /s /q env
if exist "env_new\" rmdir /s /q env_new
if exist "staticfiles\" rmdir /s /q staticfiles
if exist "db.sqlite3" del db.sqlite3
if exist "*.log" del *.log
if exist "osgeo4w-setup.exe" del osgeo4w-setup.exe

echo.
echo 3. Adding clean files...
git add .

echo.
echo 4. Committing changes...
git commit -m "Clean repository structure and fix deployment issues

- Add comprehensive .gitignore
- Remove virtual environments and build files
- Fix Gunicorn logging configuration
- Add WhiteNoise for static files
- Add DATABASE_URL support for cloud deployment
- Remove redundant files and configurations"

echo.
echo 5. Pushing to GitHub...
git push origin main

echo.
echo Repository updated successfully!
pause