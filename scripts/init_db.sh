#!/bin/bash

# Database initialization script
# Runs migrations and loads sample data

set -e

echo "🗄️  Initializing database..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U auction_user; do
  sleep 1
done

echo "✅ PostgreSQL is ready"

# Run Alembic migrations
echo "Running migrations..."
docker-compose exec -T backend alembic upgrade head

echo "✅ Migrations complete"

# Load sample data
echo "Loading sample data..."
docker-compose exec -T backend python /app/scripts/sample_data.py 50

echo "✅ Database initialized successfully!"
