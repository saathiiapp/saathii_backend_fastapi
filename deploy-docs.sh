#!/bin/bash

# Deploy Saathii Documentation
# This script builds and deploys the documentation using Docker Compose

set -e

echo "🚀 Deploying Saathii Documentation..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Build and start the docs service
echo "📦 Building documentation..."
docker-compose build docs

echo "🌐 Starting documentation service..."
docker-compose up -d docs

# Check if the service is running
echo "⏳ Waiting for documentation to be ready..."
sleep 10

# Check service status
if docker-compose ps docs | grep -q "Up"; then
    echo "✅ Documentation deployed successfully!"
    echo "🌍 Documentation is available at: https://docs.saathiiapp.com"
    echo "📊 API Documentation: https://saathiiapp.com/docs"
    echo ""
    echo "📋 Service Status:"
    docker-compose ps docs
else
    echo "❌ Documentation deployment failed!"
    echo "📋 Service Status:"
    docker-compose ps docs
    echo "📝 Logs:"
    docker-compose logs docs
    exit 1
fi

echo ""
echo "🎉 Deployment complete! Your documentation is now live."
