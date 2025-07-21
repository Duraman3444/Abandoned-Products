#!/bin/bash
# Docker Testing Script for SchoolDriver Modern
# Run this script to verify Docker configuration works properly

set -e  # Exit on any error

echo "🐳 Testing SchoolDriver Modern Docker Configuration"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   - macOS: https://docs.docker.com/desktop/mac/"
    echo "   - Linux: https://docs.docker.com/engine/install/"
    echo "   - Windows: https://docs.docker.com/desktop/windows/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if we're in the correct directory
if [ ! -f "docker/Dockerfile" ] || [ ! -f "docker/docker-compose.yml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "✅ Found Docker configuration files"

# Validate Docker configurations
echo "🔍 Validating Docker configurations..."
python3 docker/validate_config.py
if [ $? -ne 0 ]; then
    echo "❌ Docker configuration validation failed"
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f docker/Dockerfile -t schooldriver-modern:test .
if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Test that the image can run
echo "🚀 Testing Docker container..."
CONTAINER_ID=$(docker run -d -p 8080:8000 \
    -e SECRET_KEY=test-key-for-docker-testing \
    -e DEBUG=True \
    -e ALLOWED_HOSTS=localhost,127.0.0.1 \
    schooldriver-modern:test)

if [ $? -ne 0 ]; then
    echo "❌ Failed to start Docker container"
    exit 1
fi

echo "Container ID: $CONTAINER_ID"

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Test health check endpoint
echo "🏥 Testing health check endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health/ || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check endpoint working (HTTP $HTTP_CODE)"
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "Container logs:"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID > /dev/null
    docker rm $CONTAINER_ID > /dev/null
    exit 1
fi

# Test main login page
echo "🔐 Testing login page..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/accounts/login/ || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Login page accessible (HTTP $HTTP_CODE)"
else
    echo "❌ Login page failed (HTTP $HTTP_CODE)"
    echo "Container logs:"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID > /dev/null
    docker rm $CONTAINER_ID > /dev/null
    exit 1
fi

# Cleanup
echo "🧹 Cleaning up test container..."
docker stop $CONTAINER_ID > /dev/null
docker rm $CONTAINER_ID > /dev/null

echo ""
echo "🎉 All Docker tests passed!"
echo ""
echo "Next steps:"
echo "1. Test full docker-compose setup:"
echo "   cd docker && docker-compose up --build"
echo ""
echo "2. Access the application:"
echo "   - Web: http://localhost:8080"
echo "   - Health: http://localhost:8080/health/"
echo ""
echo "3. To stop: docker-compose down"
