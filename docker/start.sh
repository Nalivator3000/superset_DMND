#!/bin/bash
set -ex

echo "=== Starting Superset ==="
echo "Environment variables:"
echo "PORT: ${PORT:-8088}"
echo "DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "REDIS_URL: ${REDIS_URL:0:40}..."
echo "SUPERSET_CONFIG_PATH: ${SUPERSET_CONFIG_PATH}"

# Run migrations
echo "Running database migrations..."
superset db upgrade

# Create admin user if it doesn't exist
echo "Ensuring admin user exists..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
  --firstname "Admin" \
  --lastname "User" \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" 2>/dev/null || echo "Admin user already exists or was created"

# Initialize Superset
echo "Initializing Superset..."
superset init

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn \
  --bind "0.0.0.0:${PORT:-8088}" \
  --workers ${GUNICORN_WORKERS:-4} \
  --worker-class gevent \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --limit-request-line 0 \
  --limit-request-field_size 0 \
  --access-logfile - \
  --error-logfile - \
  "superset.app:create_app()"
