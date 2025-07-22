#!/bin/bash

# Wait for database to be ready
echo "Setting up database..."

# Run database migrations
python manage.py migrate --run-syncdb

# Load the database backup if it exists
if [ -f "database_backup.json" ]; then
    echo "Loading database backup..."
    python manage.py loaddata database_backup.json
    echo "Database backup loaded successfully!"
else
    echo "No database backup found, creating superuser..."
    # Create superuser if backup doesn't exist
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Start the Django application
echo "Starting SchoolDriver Modern..."
python manage.py runserver 0.0.0.0:8080 