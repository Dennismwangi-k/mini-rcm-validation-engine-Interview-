# Render Single Instance Deployment (Backend + Frontend)

## ✅ Yes, Render Supports Docker!

You can deploy both backend and frontend in a **single instance** using Docker. Here's how:

---

## 🐳 Docker Configuration for Single Instance

### Option 1: Combined Dockerfile (Recommended)

I've created a `Dockerfile` in the root directory that:
1. Builds the React frontend
2. Serves it with Nginx
3. Runs Django backend with Gunicorn
4. Proxies API requests from frontend to backend

### Render Settings:

**Service Type:** Web Service  
**Environment:** Docker

**Configuration:**

1. **Root Directory:** (Leave empty - uses repo root)

2. **Dockerfile Path:**
   ```
   Dockerfile
   ```
   (This is in the root of your repo)

3. **Docker Build Context Directory:**
   ```
   .
   ```
   (Root directory)

4. **Docker Command:** (Leave empty - uses Dockerfile CMD)

5. **Pre-Deploy Command:** (Optional)
   ```
   (Not needed - migrations run in startup script)
   ```

---

## 📋 Complete Render Configuration

### Build & Deploy Settings:

- **Repository:** Your GitHub repo URL
- **Branch:** `main` (or your default branch)
- **Root Directory:** (Empty - root of repo)
- **Dockerfile Path:** `Dockerfile`
- **Docker Build Context Directory:** `.`
- **Docker Command:** (Empty - uses Dockerfile CMD)
- **Pre-Deploy Command:** (Empty - handled in Dockerfile)

### Environment Variables:

Set these in Render:

```
DATABASE_URL=<from PostgreSQL service>
CELERY_BROKER_URL=<from Redis service>
CELERY_RESULT_BACKEND=<from Redis service>
SECRET_KEY=<generate a secure key>
DEBUG=False
ALLOWED_HOSTS=your-service-name.onrender.com,*.onrender.com
CORS_ALLOWED_ORIGINS=https://your-service-name.onrender.com
OPENAI_API_KEY=<your OpenAI key, optional>
REACT_APP_API_URL=https://your-service-name.onrender.com/api
```

**Note:** The frontend will automatically use the same domain, so `REACT_APP_API_URL` should point to your service URL.

---

## 🔧 How It Works

The combined Dockerfile:

1. **Stage 1 (Frontend Builder):**
   - Uses Node.js to build React app
   - Creates production build in `/app/frontend/build`

2. **Stage 2 (Production):**
   - Uses Python base image
   - Installs Django dependencies
   - Copies built frontend to `/app/staticfiles/frontend`
   - Configures Nginx to:
     - Serve frontend at `/` (root)
     - Proxy `/api/*` to Django backend
     - Proxy `/admin/*` to Django admin
     - Proxy `/health` to health check

3. **Startup Script:**
   - Runs database migrations
   - Collects static files
   - Starts Gunicorn (Django) on port 8000
   - Starts Nginx on port 8080 (Render's $PORT)

---

## 🚀 Deployment Steps

1. **Push the Dockerfile to GitHub:**
   ```bash
   git add Dockerfile
   git commit -m "Add combined Dockerfile for single instance deployment"
   git push origin main
   ```

2. **Create Web Service on Render:**
   - Go to Render Dashboard → "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure Service:**
   - **Name:** `rcm-validation-engine` (or your preferred name)
   - **Environment:** Select "Docker"
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Build Context Directory:** `.`
   - **Docker Command:** (Leave empty)

4. **Set Environment Variables:**
   - Add all the environment variables listed above
   - Connect to PostgreSQL and Redis services

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically

---

## 📝 Important Notes

### Port Configuration:
- Render sets the `$PORT` environment variable
- The Dockerfile uses port 8080 (Render's default)
- Nginx listens on this port
- Django runs on 127.0.0.1:8000 (internal)

### Celery Worker:
You'll still need a **separate Background Worker** for Celery:
- Create a Background Worker service
- Use the same Dockerfile or `backend/Dockerfile`
- Override Docker Command: `celery -A rcm_project worker -l info`
- Use same environment variables

### Database & Redis:
- Create PostgreSQL database separately
- Create Redis instance separately
- Connect both to your main service and Celery worker

---

## 🔍 Alternative: Separate Services (If Needed)

If you prefer separate services:

1. **Backend Service:**
   - Dockerfile: `backend/Dockerfile`
   - Build Context: `backend`
   - Command: `gunicorn rcm_project.wsgi:application --bind 0.0.0.0:$PORT`

2. **Frontend Service:**
   - Type: Static Site
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`
   - Root Directory: `frontend`

---

## ✅ Advantages of Single Instance

- ✅ **Cost Effective:** One service instead of two
- ✅ **Simpler Setup:** One configuration to manage
- ✅ **Same Domain:** No CORS issues
- ✅ **Easier Deployment:** Single deploy process

## ⚠️ Considerations

- **Scaling:** Both frontend and backend scale together
- **Resource Usage:** Shares CPU/memory between frontend and backend
- **Celery:** Still needs separate worker service

---

## 🐛 Troubleshooting

**Build Fails:**
- Check Dockerfile path is correct
- Verify build context includes all needed files

**Frontend Not Loading:**
- Check Nginx configuration
- Verify frontend build completed successfully

**API Not Working:**
- Check proxy configuration in Nginx
- Verify Django is running on port 8000
- Check CORS settings in Django

**Port Issues:**
- Render uses `$PORT` environment variable
- Make sure Nginx listens on `$PORT` or 8080

---

**Ready to deploy!** 🚀

Your single instance will serve both frontend and backend from one URL!

