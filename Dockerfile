# SchoolDriver Modern - Production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=schooldriver_modern.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY schooldriver-modern/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY schooldriver-modern/ .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create static files directory and collect static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput

# Create media files directory
RUN mkdir -p /app/media

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=10)" || exit 1

# Run entrypoint script
CMD ["./entrypoint.sh"]
