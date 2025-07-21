#!/bin/bash

# Kill any existing server on port 8000
echo "Stopping any existing server..."
pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
sleep 2

# Check if port is still in use
if lsof -i :8000 >/dev/null 2>&1; then
    echo "Port 8000 is still in use. Waiting..."
    sleep 3
fi

# Activate virtual environment and run Django development server
echo "Starting Django development server..."
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000

echo "Server should be available at http://127.0.0.1:8000/dashboard/"
