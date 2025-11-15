# Quick Start Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL (or use SQLite for quick testing)
- Redis (for Celery, optional for basic testing)

## Quick Setup (5 minutes)

### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

### 2. Start Backend Services

**Terminal 1 - Django Server:**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Celery Worker (if using Redis):**
```bash
cd backend
source venv/bin/activate
celery -A rcm_project worker -l info
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- Health Check: http://localhost:8000/health

## First Steps

1. **Register/Login**: Go to http://localhost:3000 and create an account
2. **Upload Claims File**: Use the provided Excel file in `data/artifacts/`
3. **View Results**: Check the Results tab for charts and detailed claims

## Using SQLite (No PostgreSQL setup needed)

The default Django settings use SQLite, so you can skip PostgreSQL setup for quick testing. Just run:

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py runserver
```

## Using Docker (Easiest)

```bash
docker-compose up --build
```

This starts everything automatically!

## Troubleshooting

### Port already in use
- Change Django port: `python manage.py runserver 8001`
- Change React port: `PORT=3001 npm start`

### Celery not working
- Make sure Redis is running: `redis-server`
- Or skip Celery for now (processing will be synchronous)

### Database errors
- Run migrations: `python manage.py migrate`
- Check database settings in `backend/rcm_project/settings.py`

## Testing the API

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Health check
curl http://localhost:8000/health/
```

## Next Steps

- Read the full README.md for detailed documentation
- Check the API documentation at http://localhost:8000/api/
- Explore the admin panel at http://localhost:8000/admin

