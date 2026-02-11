#!/bin/bash
set -e

echo "=== Superset Initialization Script ==="

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z ${POSTGRES_HOST:-postgres} ${POSTGRES_PORT:-5432}; do
  sleep 1
done
echo "Database is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
superset db upgrade

# Create admin user if not exists
echo "Creating admin user..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
  --firstname "Admin" \
  --lastname "User" \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true

# Initialize Superset
echo "Initializing Superset..."
superset init

# Load examples if requested
if [ "${SUPERSET_LOAD_EXAMPLES:-false}" = "true" ]; then
  echo "Loading example data..."
  superset load_examples
fi

echo "=== Initialization Complete ==="
