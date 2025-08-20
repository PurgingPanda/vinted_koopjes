#!/bin/bash
# Vinted Price Watch Startup Script
echo "🚀 Starting Vinted Price Watch System..."

# Activate virtual environment
source venv/bin/activate

# Start Django server in background
echo "📡 Starting Django server on port 8000..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Wait a moment for Django to start
sleep 2

# Start background task processor (blocking)
echo "🔄 Starting background task processor..."
echo "✅ System ready! Django: http://localhost:8000"
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to clean shutdown
trap "echo '🛑 Shutting down...'; kill $DJANGO_PID; exit" INT

# Start background tasks (this blocks)
python manage.py process_tasks