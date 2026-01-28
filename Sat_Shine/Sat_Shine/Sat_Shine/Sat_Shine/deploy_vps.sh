#!/bin/bash
# SAT-SHINE VPS Deployment Script

set -e

# Configuration
PROJECT_NAME="sat-shine"
PROJECT_DIR="/var/www/$PROJECT_NAME"
REPO_URL="https://github.com/yourusername/sat-shine.git"
DOMAIN="your-domain.com"
DB_NAME="sat_shine_prod"
DB_USER="sat_shine_user"

echo "🚀 Starting SAT-SHINE VPS Deployment"
echo "======================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib \
    postgis postgresql-postgis redis-server git curl supervisor certbot python3-certbot-nginx \
    build-essential libpq-dev gdal-bin libgdal-dev python3-gdal

# Create project user
echo "👤 Creating project user..."
sudo useradd --system --shell /bin/bash --home $PROJECT_DIR --create-home $PROJECT_NAME || true
sudo usermod -a -G www-data $PROJECT_NAME

# Clone repository
echo "📥 Cloning repository..."
sudo -u $PROJECT_NAME git clone $REPO_URL $PROJECT_DIR || true
cd $PROJECT_DIR

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
sudo -u $PROJECT_NAME python3 -m venv venv
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install -r requirements.txt
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install gunicorn psycopg2-binary

# Setup PostgreSQL
echo "🗄️  Setting up PostgreSQL database..."
sudo -u postgres createuser --createdb $DB_USER || true
sudo -u postgres createdb --owner=$DB_USER $DB_NAME || true
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS postgis;" $DB_NAME || true
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p /var/log/$PROJECT_NAME
sudo mkdir -p /var/run/$PROJECT_NAME
sudo chown -R $PROJECT_NAME:www-data /var/log/$PROJECT_NAME
sudo chown -R $PROJECT_NAME:www-data /var/run/$PROJECT_NAME

# Environment variables
echo "🔧 Setting up environment variables..."
sudo -u $PROJECT_NAME tee $PROJECT_DIR/.env << EOF
DJANGO_ENVIRONMENT=production
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
EOF

# Django setup
echo "🔧 Setting up Django..."
cd $PROJECT_DIR
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py migrate

# Create superuser
echo "👤 Creating Django superuser..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py shell << EOF
from authe.models import CustomUser
if not CustomUser.objects.filter(employee_id='MP0001').exists():
    CustomUser.objects.create_superuser(
        employee_id='MP0001',
        email='admin@sat-shine.com',
        password='admin123',
        first_name='ADMIN',
        last_name='USER'
    )
    print('Superuser created: MP0001 / admin123')
else:
    print('Superuser already exists')
EOF

# Setup Gunicorn service
echo "🔧 Setting up Gunicorn service..."
sudo cp $PROJECT_DIR/sat-shine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sat-shine
sudo systemctl start sat-shine

# Setup Nginx
echo "🔧 Setting up Nginx..."
sudo cp $PROJECT_DIR/nginx_sat_shine.conf /etc/nginx/sites-available/$PROJECT_NAME
sudo sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/$PROJECT_NAME
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Setup firewall
echo "🔥 Setting up firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Test PostgreSQL connection
echo "🧪 Testing PostgreSQL + PostGIS connection..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python $PROJECT_DIR/test_postgresql.py

echo "✅ Deployment completed successfully!"
echo "🌐 Your application is available at: https://$DOMAIN"
echo "🔑 Admin login: MP0001 / admin123"
echo ""
echo "📋 Next steps:"
echo "1. Update DNS records to point to this server"
echo "2. Change default admin password"
echo "3. Configure email settings in production.py"
echo "4. Set up monitoring and backups"