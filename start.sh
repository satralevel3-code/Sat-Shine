#!/bin/bash
set -e

echo "Starting SAT-SHINE deployment..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create admin user
echo "Creating admin user..."
python create_admin.py

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn Sat_Shine.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120