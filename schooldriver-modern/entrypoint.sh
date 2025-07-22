#!/bin/bash
set -e

echo "Starting SchoolDriver Modern entrypoint..."

# Start the Django server in the background first so Cloud Run doesn't timeout
python manage.py runserver 0.0.0.0:8080 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Now run database setup in the background
(
  echo "Running database migrations..."
  python manage.py migrate --run-syncdb
  
  echo "Ensuring admin user exists..."
  python manage.py ensure_admin
  
  echo "Loading sample data (optional)..."
  python manage.py loaddata database_backup.json || echo "⚠️  Sample data loading skipped (this is normal)"
  
  echo "🎉 Database setup complete!"
  echo "🔗 You can now login at: https://schooldriver-modern-dev.web.app/"
  echo "🔑 Username: admin | Password: admin123"
) &

# Wait for the main server process
wait $SERVER_PID 