#!/bin/bash
set -e

echo "Starting SchoolDriver Modern entrypoint..."

# Start the Django server in the background first so Cloud Run doesn't timeout
python manage.py runserver 0.0.0.0:8080 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Now run database setup in the background
(
  echo "Running database migrations..."
  python manage.py migrate --run-syncdb
  
  echo "Loading database backup..."
  python manage.py loaddata database_backup.json || echo "Database backup load failed, creating admin user..."
  
  # Create admin user if backup failed
  python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Admin user created successfully')
else:
    print('Admin user already exists')
" || echo "Admin user creation handled"
  
  echo "Database setup complete!"
) &

# Wait for the main server process
wait $SERVER_PID 