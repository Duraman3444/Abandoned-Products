#!/bin/bash

echo "Checking server status on port 8000..."

if lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ Server is running on port 8000"
    echo "Testing dashboard endpoint..."
    
    if curl -s http://127.0.0.1:8000/dashboard/ | grep -q "Dashboard"; then
        echo "✅ Dashboard is accessible at http://127.0.0.1:8000/dashboard/"
    else
        echo "❌ Dashboard endpoint not working"
    fi
    
    echo "Testing Chart.js static file..."
    if curl -s -I http://127.0.0.1:8000/static/js/chart.min.js | grep -q "200 OK"; then
        echo "✅ Chart.js static file is accessible"
    else
        echo "❌ Chart.js static file not accessible"
    fi
    
else
    echo "❌ No server running on port 8000"
    echo "To start the server, run: ./run_server.sh"
fi
