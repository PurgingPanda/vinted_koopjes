#!/bin/bash

# Vinted Koopjes Django Application Setup Script
# This script sets up the development environment for a new computer

echo "Setting up Vinted Koopjes Django application..."

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install requirements
echo "Activating virtual environment and installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create static directory
echo "Creating static directory..."
mkdir -p static

# Run any pending migrations
echo "Creating and applying migrations..."
python manage.py makemigrations
python manage.py migrate

# Reset admin password using custom script
echo "Setting up admin user with default credentials..."
python reset_admin_password.py

echo ""
echo "Setup complete! 🚀"
echo ""
echo "✨ Features available:"
echo "  • Price watch monitoring"
echo "  • Statistical underprice detection"
echo "  • AI-powered item clustering"
echo "  • Background task processing"
echo "  • Email alerts"
echo ""
echo "Default admin credentials:"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "To start the application:"
echo "1. Use the start script: ./start_all.sh"
echo "   OR manually:"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start Django server: python manage.py runserver"
echo "4. Start background scraping: python manage.py process_tasks (in another terminal)"
echo ""
echo "Access the app at: http://127.0.0.1:8080"
echo "Admin panel at: http://127.0.0.1:8080/admin/"
echo ""
echo "🤖 To test clustering: python manage.py test_clustering <watch_id>"