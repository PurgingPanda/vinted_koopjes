#!/bin/bash

# Vinted Koopjes - Start All Services Script
# This script starts both the Django development server and background task processor

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Vinted Koopjes Application...${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run ./setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for critical dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
python -c "import django, pytz, playwright, requests, httpx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing dependencies detected. Running pip install...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install dependencies. Please run ./setup.sh${NC}"
        exit 1
    fi
fi

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    # Kill all background jobs
    jobs -p | xargs -r kill
    echo -e "${GREEN}✅ All services stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}🌐 Starting Django development server...${NC}"
python manage.py runserver --settings=settings_spitsboog &
SERVER_PID=$!

echo -e "${GREEN}⚙️  Starting background task processor...${NC}"
python manage.py process_tasks --settings=settings_spitsboog &
TASKS_PID=$!

echo ""
echo -e "${BLUE}📊 Services Status:${NC}"
echo -e "  • Django Server: ${GREEN}Running${NC} (PID: $SERVER_PID) - http://127.0.0.1:8000"
echo -e "  • Background Tasks: ${GREEN}Running${NC} (PID: $TASKS_PID)"
echo ""
echo -e "${YELLOW}📝 Useful URLs:${NC}"
echo -e "  • Dashboard: http://127.0.0.1:8000"
echo -e "  • Admin Panel: http://127.0.0.1:8000/admin/"
echo -e "  • Token Injection: http://127.0.0.1:8000/token/inject/"
echo ""
echo -e "${YELLOW}⚡ Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for background jobs to complete (they won't unless killed)
wait