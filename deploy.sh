#!/bin/bash

# Vinted Koopjes Server Deployment Script
# This script sets up the application on a Ubuntu server with Tailscale-only access

set -e  # Exit on any error

echo "🚀 Starting Vinted Koopjes Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run as root. Run as a regular user with sudo access."
    exit 1
fi

# Install Tailscale if not already installed
if ! command -v tailscale &> /dev/null; then
    print_status "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "Please run 'sudo tailscale up' to connect this machine to your Tailnet"
    read -p "Press enter after you've connected to Tailscale..."
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    supervisor \
    postgresql \
    postgresql-contrib \
    chromium-browser \
    git \
    curl \
    ufw

# Create application user
if ! id "vinted" &>/dev/null; then
    print_status "Creating vinted user..."
    sudo useradd -m -s /bin/bash vinted
fi

# Setup application directory
APP_DIR="/opt/vinted_koopjes"
print_status "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown vinted:vinted $APP_DIR

# Copy application files (assuming this script is run from the app directory)
print_status "Copying application files..."
sudo cp -r . $APP_DIR/
sudo chown -R vinted:vinted $APP_DIR

# Switch to application directory
cd $APP_DIR

# Create Python virtual environment
print_status "Creating Python virtual environment..."
sudo -u vinted python3 -m venv venv
sudo -u vinted $APP_DIR/venv/bin/pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
sudo -u vinted $APP_DIR/venv/bin/pip install -r requirements.txt
sudo -u vinted $APP_DIR/venv/bin/pip install gunicorn psycopg2-binary

# Setup PostgreSQL database
print_status "Setting up PostgreSQL database..."
sudo -u postgres createuser --createdb vinted 2>/dev/null || true
sudo -u postgres createdb vinted_db -O vinted 2>/dev/null || true

# Generate Django secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Create environment file
print_status "Creating environment configuration..."
sudo -u vinted tee $APP_DIR/.env > /dev/null <<EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://vinted@localhost/vinted_db
ALLOWED_HOSTS=*
TAILSCALE_ONLY=True
EOF

# Run Django migrations
print_status "Running database migrations..."
sudo -u vinted $APP_DIR/venv/bin/python manage.py migrate

# Collect static files
print_status "Collecting static files..."
sudo -u vinted $APP_DIR/venv/bin/python manage.py collectstatic --noinput

# Create Django superuser
print_warning "Creating Django superuser..."
echo "You'll need to create an admin user:"
sudo -u vinted $APP_DIR/venv/bin/python manage.py createsuperuser

# Configure Nginx
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/vinted_koopjes > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    
    # Only allow Tailscale IPs (100.x.x.x range)
    allow 100.64.0.0/10;
    deny all;
    
    location /static/ {
        alias /opt/vinted_koopjes/staticfiles/;
    }
    
    location /media/ {
        alias /opt/vinted_koopjes/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/vinted_koopjes /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure Supervisor for Django and background tasks
print_status "Configuring Supervisor..."
sudo tee /etc/supervisor/conf.d/vinted_koopjes.conf > /dev/null <<EOF
[program:vinted_web]
command=$APP_DIR/venv/bin/gunicorn vinted_koopjes.wsgi:application --bind 127.0.0.1:8000 --workers 2
directory=$APP_DIR
user=vinted
autostart=true
autorestart=true
stderr_logfile=/var/log/vinted_koopjes_web.err.log
stdout_logfile=/var/log/vinted_koopjes_web.out.log

[program:vinted_tasks]
command=$APP_DIR/venv/bin/python manage.py process_tasks
directory=$APP_DIR
user=vinted
autostart=true
autorestart=true
stderr_logfile=/var/log/vinted_koopjes_tasks.err.log
stdout_logfile=/var/log/vinted_koopjes_tasks.out.log
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow from 100.64.0.0/10 to any port 80  # Allow Tailscale network
sudo ufw allow from 100.64.0.0/10 to any port 22   # SSH from Tailscale
sudo ufw deny 80  # Deny public HTTP access
sudo ufw deny 22   # Deny public SSH access

# Enable services
sudo systemctl enable nginx supervisor

print_status "Deployment completed!"
echo ""
print_warning "Next steps:"
echo "1. Your Vinted Koopjes app is running at: http://$(tailscale ip -4):80"
echo "2. Only accessible via your Tailscale network"
echo "3. Check logs with: sudo supervisorctl tail -f vinted_web"
echo "4. Restart services with: sudo supervisorctl restart all"
echo ""
print_status "Deployment finished successfully! 🎉"