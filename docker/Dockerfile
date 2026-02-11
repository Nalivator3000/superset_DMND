# Apache Superset Production Dockerfile
# Based on official image with additional database drivers

FROM apache/superset:6.0.0

USER root

# Install system dependencies for database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    freetds-dev \
    freetds-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install database drivers using uv (Superset 6.0 uses uv instead of pip)
# Keep running as root to avoid permission issues with venv
RUN uv pip install --no-cache-dir \
    psycopg2-binary \
    mysqlclient \
    clickhouse-connect \
    pymssql \
    redis \
    gevent

# Switch to superset user
USER superset

# Copy custom configuration and scripts
COPY --chown=superset:superset docker/superset_config.py /app/superset_config.py
COPY --chown=superset:superset docker/start.sh /app/docker/start.sh
COPY --chown=superset:superset docker/superset-init.sh /app/docker/superset-init.sh

# Make scripts executable
USER root
RUN chmod +x /app/docker/start.sh /app/docker/superset-init.sh
USER superset

# Set environment variable for config
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Expose port
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1
