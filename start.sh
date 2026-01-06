#!/bin/bash
set -e

echo "Starting SAT-SHINE deployment..."

# Backup existing data if database exists
echo "Backing up existing data..."
if [ -f "db.sqlite3" ]; then
    python data_backup.py backup
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create admin user
echo "Creating/updating admin user..."
python create_admin.py

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn Sat_Shine.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -