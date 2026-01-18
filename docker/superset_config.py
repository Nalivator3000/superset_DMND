"""
Apache Superset Production Configuration
Optimized for Railway deployment with PostgreSQL and Redis
"""

import os
from datetime import timedelta
from celery.schedules import crontab

# =============================================================================
# CORE SETTINGS
# =============================================================================

# IMPORTANT: Generate a strong secret key for production
# openssl rand -base64 42
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("SUPERSET_SECRET_KEY") or "kZ8h9L2mN5pQ7rS0tU3vW6xY9aB1cD4eF7gH0iJ3kL6mN9oP2qR5sT8uV1wX4yZ7"

# JWT secret for async queries (must be at least 32 bytes)
GLOBAL_ASYNC_QUERIES_JWT_SECRET = SECRET_KEY

# Application name
APP_NAME = "Superset DMND"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Metadata database (PostgreSQL)
# Railway provides DATABASE_URL automatically
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Railway uses postgres:// but SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    # Local development fallback
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "superset")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "superset")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "superset")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# =============================================================================
# REDIS / CACHE CONFIGURATION
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    REDIS_HOST = REDIS_URL
else:
    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Cache configuration - use simple cache if Redis not available
if REDIS_URL and REDIS_URL not in ("redis://", "none", ""):
    CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 300,
        "CACHE_KEY_PREFIX": "superset_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
    DATA_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
        "CACHE_KEY_PREFIX": "superset_data_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
    FILTER_STATE_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
        "CACHE_KEY_PREFIX": "superset_filter_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
    EXPLORE_FORM_DATA_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
        "CACHE_KEY_PREFIX": "superset_explore_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
else:
    # Fallback to simple in-memory cache
    CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300,
    }
    DATA_CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
    }
    FILTER_STATE_CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
    }
    EXPLORE_FORM_DATA_CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
    }

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

if REDIS_URL and REDIS_URL not in ("redis://", "none", ""):
    class CeleryConfig:
        broker_url = REDIS_URL
        result_backend = REDIS_URL
        worker_prefetch_multiplier = 1
        task_acks_late = True
        task_annotations = {
            "sql_lab.get_sql_results": {
                "rate_limit": "100/s",
            },
        }
        beat_schedule = {
            "reports.scheduler": {
                "task": "reports.scheduler",
                "schedule": crontab(minute="*", hour="*"),
            },
            "reports.prune_log": {
                "task": "reports.prune_log",
                "schedule": crontab(minute=0, hour=0),
            },
        }

    CELERY_CONFIG = CeleryConfig
else:
    CELERY_CONFIG = None

# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ESCAPE_MARKDOWN_HTML": True,
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "SCHEDULED_QUERIES": True,
    "SQL_VALIDATORS_BY_ENGINE": True,
    "THUMBNAILS": False,
    "GLOBAL_ASYNC_QUERIES": False,  # Disabled - requires results backend
}

# Results backend for async queries (using Redis)
RESULTS_BACKEND = None  # Disable async results

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# CSRF protection
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365  # 1 year

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
SESSION_COOKIE_HTTPONLY = True

# Content Security Policy
TALISMAN_ENABLED = False  # Enable if you need strict CSP

# =============================================================================
# SQL LAB SETTINGS
# =============================================================================

SQLLAB_TIMEOUT = 300
SQLLAB_DEFAULT_DBID = None
SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 60 * 6  # 6 hours

# Enable SQL Lab
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000

# =============================================================================
# WEB SERVER SETTINGS
# =============================================================================

# Server name for URL generation
# Set this to your Railway domain
SUPERSET_WEBSERVER_PROTOCOL = os.environ.get("SUPERSET_WEBSERVER_PROTOCOL", "https")
SUPERSET_WEBSERVER_ADDRESS = os.environ.get("SUPERSET_WEBSERVER_ADDRESS", "0.0.0.0")
SUPERSET_WEBSERVER_PORT = int(os.environ.get("PORT", 8088))

# Enable proxy fix for Railway (behind load balancer)
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {
    "x_for": 1,
    "x_proto": 1,
    "x_host": 1,
    "x_prefix": 1,
}

# =============================================================================
# LOGGING
# =============================================================================

LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# =============================================================================
# MISC SETTINGS
# =============================================================================

# Row limit for queries
ROW_LIMIT = 50000

# Default language
BABEL_DEFAULT_LOCALE = "en"

# Supported languages
LANGUAGES = {
    "en": {"flag": "us", "name": "English"},
    "ru": {"flag": "ru", "name": "Russian"},
}

# Thumbnail generation
if REDIS_URL and REDIS_URL not in ("redis://", "none", ""):
    THUMBNAIL_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
        "CACHE_KEY_PREFIX": "superset_thumb_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
else:
    THUMBNAIL_CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 86400,
    }

# Alerts & Reports
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
WEBDRIVER_BASEURL = os.environ.get("WEBDRIVER_BASEURL", "http://localhost:8088/")
