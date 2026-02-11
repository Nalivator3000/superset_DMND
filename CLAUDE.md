# Apache Superset DMND - Project Context

## Project Overview

This project deploys Apache Superset on Railway with PostgreSQL database using Docker.

**Superset Version:** 6.0.0 (latest)
**Deployment Target:** Railway.app
**Database:** PostgreSQL (managed by Railway)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Railway                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Superset   │  │  PostgreSQL │  │    Redis    │ │
│  │   (Web +    │◄─┤  (metadata) │  │   (cache)   │ │
│  │   Worker)   │  └─────────────┘  └─────────────┘ │
│  └─────────────┘                          ▲        │
│         │                                 │        │
│         └─────────────────────────────────┘        │
└─────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `docker/Dockerfile` | Custom Superset image with DB drivers |
| `docker/docker-compose.yml` | Local development setup |
| `docker/superset_config.py` | Superset configuration |
| `docker/superset-init.sh` | Initialization script |
| `railway.toml` | Railway deployment config |
| `.env.example` | Environment variables template |

## Environment Variables

### Required
- `SECRET_KEY` - Flask secret key (generate with `openssl rand -base64 42`)
- `DATABASE_URL` - PostgreSQL connection string (provided by Railway)
- `REDIS_URL` - Redis connection string (provided by Railway)

### Optional
- `SUPERSET_ADMIN_USERNAME` - Admin username (default: admin)
- `SUPERSET_ADMIN_PASSWORD` - Admin password
- `SUPERSET_ADMIN_EMAIL` - Admin email
- `SUPERSET_LOAD_EXAMPLES` - Load example dashboards (default: false)

## Commands

### Local Development
```bash
# Start all services
cd docker && docker-compose up -d

# View logs
docker-compose logs -f superset

# Stop services
docker-compose down
```

### Railway Deployment
```bash
# Login to Railway
railway login

# Link to project
railway link

# Deploy
railway up
```

## Database Drivers Included

- PostgreSQL (`psycopg2-binary`)
- MySQL (`mysqlclient`)
- ClickHouse (`clickhouse-connect`)
- MS SQL Server (`pymssql`)

## Important Notes

1. **SECRET_KEY**: Must be set and kept secret in production
2. **Database**: Use Railway's managed PostgreSQL, not a container volume
3. **Memory**: Superset requires minimum 4GB RAM (8GB recommended)
4. **Initialization**: First deployment runs migrations and creates admin user

## Troubleshooting

### Common Issues

1. **"Secret key not found"** - Set `SECRET_KEY` environment variable
2. **"Database connection failed"** - Check `DATABASE_URL` format
3. **"Worker not starting"** - Ensure Redis is connected via `REDIS_URL`

## References

- [Apache Superset Docs](https://superset.apache.org/docs/)
- [Railway Docs](https://docs.railway.com/)
- [Superset Docker Hub](https://hub.docker.com/r/apache/superset)
