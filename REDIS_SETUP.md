# Redis Setup for Celery

## Problem
Celery needs Redis to be running. If you see "Connection refused" errors, Redis is not running.

## Solution Options

### Option 1: Install and Start Redis Locally (macOS)

**Using Homebrew (Recommended):**
```bash
# Install Redis
brew install redis

# Start Redis
brew services start redis

# Or start manually (runs in foreground)
redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Option 2: Use Docker for Redis Only

```bash
# Start just Redis in Docker
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Stop it later with:
docker stop redis
docker rm redis
```

### Option 3: Use Docker Compose (Easiest - Runs Everything)

```bash
# This starts Redis, PostgreSQL, Backend, Celery, and Frontend all together
docker-compose up
```

## After Starting Redis

Once Redis is running, your Celery worker should connect successfully:

```bash
cd backend
source venv/bin/activate
celery -A rcm_project worker -l info
```

You should see:
```
[2025-11-14 20:XX:XX,XXX: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-11-14 20:XX:XX,XXX: INFO/MainProcess] celery@Macs-MacBook-Pro.local ready.
```

## Quick Check

To verify Redis is accessible:
```bash
redis-cli ping
```

If it returns `PONG`, Redis is running and Celery should connect.

## Note

If you're running everything manually (not with Docker), you need:
1. ✅ PostgreSQL (or SQLite - default)
2. ✅ Redis (for Celery)
3. ✅ Django server
4. ✅ Celery worker
5. ✅ React frontend

**OR** just use Docker Compose which handles all of this automatically! 🚀

