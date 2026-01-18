# Apache Superset Production Dockerfile
# Based on official image with additional database drivers

FROM apache/superset:6.0.0

USER root

# Install system dependencies for database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    freetds-dev \
    freetds-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to superset user for package installation
USER superset

# Install database drivers using uv (Superset 6.0 uses uv instead of pip)
RUN uv pip install --no-cache-dir \
    psycopg2-binary \
    mysqlclient \
    clickhouse-connect \
    pymssql \
    redis \
    gevent

# Copy custom configuration and scripts
COPY --chown=superset:superset superset_config.py /app/superset_config.py
COPY --chown=superset:superset start.sh /app/docker/start.sh
COPY --chown=superset:superset superset-init.sh /app/docker/superset-init.sh

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
