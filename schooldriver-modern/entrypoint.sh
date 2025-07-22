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
  
  echo "Creating/updating admin user..."
  python manage.py shell -c "
from django.contrib.auth.models import User

try:
    admin = User.objects.get(username='admin')
    print('Admin user exists, updating...')
    admin.set_password('admin123')
    admin.is_superuser = True
    admin.is_staff = True
    admin.is_active = True
    admin.email = 'admin@example.com'
    admin.save()
    print('✅ Admin user updated successfully')
except User.DoesNotExist:
    print('Creating new admin user...')
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Admin user created successfully')

print(f'👤 Username: {admin.username}')
print(f'🔑 Password: admin123')
print(f'👑 Superuser: {admin.is_superuser}')
print(f'📋 Staff: {admin.is_staff}')
print(f'✅ Active: {admin.is_active}')
"
  
  echo "Loading sample data (optional)..."
  python manage.py loaddata database_backup.json || echo "⚠️  Sample data loading skipped (this is normal)"
  
  echo "🎉 Database setup complete!"
  echo "🔗 You can now login with: admin / admin123"
) &

# Wait for the main server process
wait $SERVER_PID 