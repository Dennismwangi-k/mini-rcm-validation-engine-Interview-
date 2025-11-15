# Docker Setup Guide

## ✅ Yes! Docker runs everything at once!

When you run `docker-compose up`, it will start **ALL** services automatically:

1. **PostgreSQL Database** (port 5432)
2. **Redis** (port 6379)
3. **Django Backend** (port 8000)
4. **Celery Worker** (background processing)
5. **React Frontend** (port 3000)

## Quick Start with Docker

### 1. Create .env file (if not exists)
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY if you want LLM features
```

### 2. Start everything
```bash
docker-compose up --build
```

That's it! All services will start automatically.

### 3. Access the application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health

## What happens automatically:

1. **Database**: PostgreSQL starts and waits to be ready
2. **Redis**: Starts for Celery message broker
3. **Backend**: 
   - Waits for database to be healthy
   - Runs migrations automatically
   - Starts Django server
4. **Celery**: 
   - Waits for database and Redis
   - Runs migrations
   - Starts worker for async tasks
5. **Frontend**: 
   - Waits for backend
   - Starts React dev server

## Viewing Logs

To see logs from all services:
```bash
docker-compose up
```

To see logs from specific service:
```bash
docker-compose logs backend
docker-compose logs celery
docker-compose logs frontend
```

## Stopping Services

Press `Ctrl+C` to stop, or:
```bash
docker-compose down
```

To stop and remove volumes (clears database):
```bash
docker-compose down -v
```

## Rebuilding After Changes

If you make code changes:
```bash
docker-compose up --build
```

## Troubleshooting

### Port already in use
If ports 3000, 8000, 5432, or 6379 are in use, stop those services first.

### Database connection errors
The backend waits for the database to be healthy before starting. If you see connection errors, wait a few seconds.

### Frontend can't connect to backend
Make sure backend is running and accessible at http://localhost:8000

### Celery not processing tasks
Check that Redis is running: `docker-compose logs redis`

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| frontend | 3000 | React UI |
| backend | 8000 | Django API |
| db | 5432 | PostgreSQL |
| redis | 6379 | Celery broker |
| celery | - | Background worker |

## Environment Variables

Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key
DEBUG=1
OPENAI_API_KEY=your-key-here  # Optional
```

The docker-compose.yml will automatically use these variables.

## Benefits of Docker Setup

✅ **One command** to start everything  
✅ **No manual setup** of PostgreSQL, Redis, etc.  
✅ **Consistent environment** across machines  
✅ **Easy deployment** - same setup works everywhere  
✅ **Isolated** - doesn't affect your system  

## Production Deployment

For production, you would:
1. Set `DEBUG=0` in .env
2. Use production database credentials
3. Set up proper SSL/HTTPS
4. Use production-ready web server (gunicorn, nginx)
5. Set up proper volume mounts for persistent data

But for the assessment, the current Docker setup is perfect! 🚀

