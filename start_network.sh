#!/bin/bash

# Start Network Interception Scraper for Vinted Price Watch
# This script sets up the environment for network interception mode and starts the Django application

echo "🌐 Starting Vinted Price Watch with Network Interception Scraper..."

# Set environment variable for network interception mode
export VINTED_SCRAPER_MODE=network

# Set Django settings
export DJANGO_SETTINGS_MODULE=settings_spitsboog

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found. Make sure dependencies are installed globally."
fi

# Check if Playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo "❌ Playwright not found. Installing..."
    pip install playwright
    playwright install chromium
fi

# Check if network scraper components are available
echo "🔍 Checking network interception scraper availability..."
python -c "
import os
os.environ['VINTED_SCRAPER_MODE'] = 'network'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_spitsboog'

try:
    import django
    django.setup()
    
    import sys
    sys.path.insert(0, 'vinted_scraper/src')
    
    from vinted_scraper import VintedScraper
    print('✅ Network interception scraper is ready!')
    print(f'📍 Using scraper: {VintedScraper.__name__}')
except Exception as e:
    print(f'❌ Network scraper check failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Network scraper is not ready. Please check the installation."
    exit 1
fi

echo ""
echo "🚀 Starting Django server with Network Interception mode..."
echo "📍 Server will be available at: http://spitsboog.org:8080"
echo "🌐 Scraper mode: Network Interception (maximum stealth)"
echo ""
echo "🔥 Features enabled:"
echo "   • Network request/response interception"
echo "   • Natural cookie acquisition (no manual injection)"  
echo "   • Maximum stealth browsing"
echo "   • Human-like behavior simulation"
echo "   • API call capture from browser traffic"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Network Interception scraper..."
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start the Django development server with background tasks
echo "Starting Django server and background task processor..."

# Start background task processor in the background (with venv)
VINTED_SCRAPER_MODE=network ./venv/bin/python manage.py process_tasks --settings=settings_spitsboog > tasks.log 2>&1 &
TASKS_PID=$!

# Start Django server in the background (with venv)
VINTED_SCRAPER_MODE=network ./venv/bin/python manage.py runserver 0.0.0.0:8080 --settings=settings_spitsboog &
SERVER_PID=$!

# Show URL logging in real-time
echo "📺 Showing real-time URL navigation logs..."
echo "   (Network interception scraper activity will appear below)"
echo ""

# Filter and display URL-related logs from tasks.log in real-time
tail -f tasks.log | grep --line-buffered -E "🧭|📥|📍|🌐|🎯|🔧|🥷|🎭|NETWORK SCRAPER|DJANGO SERVICE|ACTIVE SCRAPER|UTILS DEBUG|FORCED NETWORK|TARGET URL|STARTING BROWSER|NAVIGATION COMPLETED|playwright-stealth|Selected user agent|NetworkInterception|navigation|URL|Starting navigation|Navigation response|Current page URL|Intercepted.*API|Captured.*data|Using.*scraper" &
TAIL_PID=$!

# Wait for server process (main process)
wait $SERVER_PID

# Clean up tail process
kill $TAIL_PID 2>/dev/null