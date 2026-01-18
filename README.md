# Superset DMND

Apache Superset deployment for Railway with PostgreSQL and Redis.

## Quick Start

### Local Development

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```

2. Start services:
   ```bash
   cd docker
   docker-compose up -d
   ```

3. Access Superset at http://localhost:8088
   - Username: `admin`
   - Password: `admin`

### Railway Deployment

1. Create a new project on [Railway](https://railway.app)

2. Add services:
   - PostgreSQL (from Railway's database templates)
   - Redis (from Railway's database templates)

3. Add your Superset service:
   - Connect your GitHub repository
   - Set the root directory to `docker`

4. Configure environment variables:
   ```
   SECRET_KEY=<generate with: openssl rand -base64 42>
   SUPERSET_ADMIN_USERNAME=admin
   SUPERSET_ADMIN_PASSWORD=<strong-password>
   SUPERSET_ADMIN_EMAIL=admin@yourdomain.com
   ```

5. Railway automatically provides:
   - `DATABASE_URL` (from PostgreSQL service)
   - `REDIS_URL` (from Redis service)
   - `PORT` (for web server)

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Railway                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Superset │  │ Postgres │  │  Redis   │      │
│  │  (Web)   │◄─┤(metadata)│  │ (cache)  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key |
| `DATABASE_URL` | Yes* | PostgreSQL connection string |
| `REDIS_URL` | Yes* | Redis connection string |
| `SUPERSET_ADMIN_USERNAME` | No | Admin username (default: admin) |
| `SUPERSET_ADMIN_PASSWORD` | No | Admin password (default: admin) |
| `SUPERSET_ADMIN_EMAIL` | No | Admin email |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

*Provided automatically by Railway

### Database Drivers

The Docker image includes drivers for:
- PostgreSQL
- MySQL
- ClickHouse
- MS SQL Server

## Development

### Project Structure

```
superset_DMND/
├── docker/
│   ├── Dockerfile           # Custom Superset image
│   ├── docker-compose.yml   # Local development setup
│   ├── superset_config.py   # Superset configuration
│   ├── superset-init.sh     # Initialization script
│   └── start.sh             # Startup script for Railway
├── .env.example             # Environment template
├── railway.toml             # Railway configuration
├── CLAUDE.md                # AI agent context
└── README.md
```

### Useful Commands

```bash
# View logs
docker-compose logs -f superset

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Rebuild image
docker-compose build --no-cache
```

## Troubleshooting

### "Secret key not found"
Set the `SECRET_KEY` environment variable.

### Database connection issues
Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db`

### Slow startup
First startup takes longer due to migrations. Check logs for progress.

## License

Apache License 2.0
