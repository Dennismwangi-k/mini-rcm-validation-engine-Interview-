# Render Deployment Commands

## 🚀 Quick Reference - Commands for Render Services

### 1. Backend Service (Django API)

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn rcm_project.wsgi:application --bind 0.0.0.0:$PORT
```

**Pre-Deploy Command (Optional - for migrations):**
```bash
python manage.py migrate
```

**Root Directory:**
```
backend
```

**Dockerfile Path (if using Docker):**
```
backend/Dockerfile
```

---

### 2. Celery Worker Service

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
celery -A rcm_project worker -l info
```

**Pre-Deploy Command (Optional - for migrations):**
```bash
python manage.py migrate
```

**Root Directory:**
```
backend
```

**Dockerfile Path (if using Docker):**
```
backend/Dockerfile
```

---

### 3. Frontend Service (React)

**Build Command:**
```bash
npm install && npm run build
```

**Start Command:**
```bash
npx serve -s build -l $PORT
```

**OR if using static site:**
- **Publish Directory:** `build`
- **Build Command:** `npm install && npm run build`

**Root Directory:**
```
frontend
```

**Dockerfile Path (if using Docker):**
```
frontend/Dockerfile
```

---

## 📋 Complete Configuration Summary

### Backend Service Settings:
- **Name:** `rcm-backend`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Start Command:** `gunicorn rcm_project.wsgi:application --bind 0.0.0.0:$PORT`
- **Pre-Deploy Command:** `python manage.py migrate`
- **Root Directory:** `backend`

### Celery Worker Settings:
- **Name:** `rcm-celery-worker`
- **Type:** Background Worker
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `celery -A rcm_project worker -l info`
- **Pre-Deploy Command:** `python manage.py migrate`
- **Root Directory:** `backend`

### Frontend Service Settings:
- **Name:** `rcm-frontend`
- **Type:** Static Site (or Web Service)
- **Environment:** `Node`
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npx serve -s build -l $PORT` (if Web Service)
- **Publish Directory:** `build` (if Static Site)
- **Root Directory:** `frontend`

---

## 🔧 Alternative: Using Docker

If you prefer to use Docker instead:

### Backend & Celery:
- **Dockerfile Path:** `backend/Dockerfile`
- **Docker Build Context Directory:** `backend`
- **Docker Command:** (Leave empty, uses Dockerfile CMD)

### Frontend:
- **Dockerfile Path:** `frontend/Dockerfile`
- **Docker Build Context Directory:** `frontend`
- **Docker Command:** (Leave empty, uses Dockerfile CMD)

---

## ⚙️ Environment Variables

Don't forget to set these in each service:

### Backend:
- `DATABASE_URL` (from PostgreSQL service)
- `CELERY_BROKER_URL` (from Redis service)
- `CELERY_RESULT_BACKEND` (from Redis service)
- `SECRET_KEY` (generate or use Render's generator)
- `DEBUG=False`
- `ALLOWED_HOSTS=rcm-backend.onrender.com,*.onrender.com`
- `CORS_ALLOWED_ORIGINS=https://rcm-frontend.onrender.com`
- `OPENAI_API_KEY` (optional)

### Celery Worker:
- Same as Backend (copy all env vars)

### Frontend:
- `REACT_APP_API_URL=https://rcm-backend.onrender.com/api`
- `NODE_VERSION=18.20.0`

---

## 📝 Step-by-Step Setup

1. **Create PostgreSQL Database**
   - Name: `rcm-database`
   - Save the connection string

2. **Create Redis Instance**
   - Name: `rcm-redis`
   - Save the connection string

3. **Create Backend Service**
   - Use commands above
   - Connect to PostgreSQL and Redis
   - Set environment variables

4. **Create Celery Worker**
   - Use commands above
   - Use same database and Redis as backend
   - Copy all backend env vars

5. **Create Frontend Service**
   - Use commands above
   - Set `REACT_APP_API_URL` to your backend URL

6. **Run Migrations**
   - Go to backend service → Shell
   - Run: `python manage.py migrate`
   - Run: `python manage.py createsuperuser` (optional)

---

**Ready to deploy!** 🚀

