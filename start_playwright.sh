#!/bin/bash

# Vinted Koopjes Application Startup Script with Playwright Mode
# This script starts the Django application with Playwright-based scraping for maximum stealth

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Set Playwright mode
export VINTED_SCRAPER_MODE=playwright

print_status "🎭 Starting Vinted Koopjes Application with Playwright Scraper..."
echo ""

# Activate virtual environment
print_status "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if Playwright is installed
print_status "🔍 Checking Playwright installation..."
if python -c "import playwright; print('✅ Playwright available')" 2>/dev/null; then
    print_success "✅ Playwright is installed and available"
else
    print_error "❌ Playwright not found. Installing..."
    pip install playwright
    playwright install chromium
fi

# Check dependencies
print_status "🔍 Checking dependencies..."
if [ ! -f "requirements.txt" ]; then
    print_error "❌ requirements.txt not found!"
    exit 1
fi

# Kill existing processes
print_status "🧹 Stopping any existing services..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "python manage.py process_tasks" 2>/dev/null || true
sleep 2

# Start Django server with Playwright mode
print_status "🌐 Starting Django development server on port 8080..."
export VINTED_SCRAPER_MODE=playwright
nohup ./venv/bin/python manage.py runserver 0.0.0.0:8080 --settings=settings_spitsboog > server.log 2>&1 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Start background task processor with Playwright mode  
print_status "⚙️  Starting background task processor with Playwright mode..."
export VINTED_SCRAPER_MODE=playwright
nohup ./venv/bin/python manage.py process_tasks --settings=settings_spitsboog > tasks.log 2>&1 &
TASKS_PID=$!

# Wait a moment for tasks to start
sleep 3

# Check if processes are running
print_status "📊 Checking services status..."
if ps -p $SERVER_PID > /dev/null; then
    print_success "  • Django Server: Running (PID: $SERVER_PID) - http://0.0.0.0:8080"
else
    print_error "  • Django Server: Failed to start"
fi

if ps -p $TASKS_PID > /dev/null; then
    print_success "  • Background Tasks: Running (PID: $TASKS_PID)"
else
    print_error "  • Background Tasks: Failed to start"
fi

echo ""
print_status "🎭 PLAYWRIGHT SCRAPER CONFIGURATION:"
echo "  • Mode: $VINTED_SCRAPER_MODE"
echo "  • Stealth: Maximum (anti-detection enabled)"
echo "  • Browser: Chromium headless"
echo "  • Retry Logic: Enabled with exponential backoff"

echo ""
print_warning "📝 Useful URLs:"
echo "  • Dashboard: http://spitsboog.org:8080"
echo "  • Admin Panel: http://spitsboog.org:8080/admin/"
echo "  • Token Injection: http://spitsboog.org:8080/token/inject/"

echo ""
print_warning "📋 Log Files:"
echo "  • Server Log: tail -f server.log"
echo "  • Tasks Log: tail -f tasks.log"

echo ""
print_warning "⚡ Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "🛑 Shutting down services..."
    kill $SERVER_PID 2>/dev/null || true
    kill $TASKS_PID 2>/dev/null || true
    kill $TAIL_PID 2>/dev/null || true
    print_success "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Show URL logging in real-time
print_status "📺 Showing real-time URL navigation logs..."
print_warning "   (Playwright scraper activity will appear below)"
echo ""

# Filter and display URL-related logs from tasks.log in real-time
tail -f tasks.log | grep --line-buffered -E "🧭|📥|📍|🌐|🎯|Playwright|navigation|URL|Starting navigation|Navigation response|Current page URL|goto|page\.goto" &
TAIL_PID=$!

# Keep script running and show periodic status
while true; do
    sleep 30
    
    # Check if processes are still running
    if ! ps -p $SERVER_PID > /dev/null; then
        print_error "⚠️  Django server stopped unexpectedly!"
        kill $TAIL_PID 2>/dev/null || true
        break
    fi
    
    if ! ps -p $TASKS_PID > /dev/null; then
        print_error "⚠️  Background tasks stopped unexpectedly!"
        kill $TAIL_PID 2>/dev/null || true
        break
    fi
    
    # Show a less frequent heartbeat (since URL logs provide activity)
    print_status "💓 Services running... ($(date '+%H:%M:%S'))"
done

# If we get here, something failed
cleanup