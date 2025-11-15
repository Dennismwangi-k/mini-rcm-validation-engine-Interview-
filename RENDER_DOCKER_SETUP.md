# 🐳 Render Docker Deployment - Single Instance

## ✅ Yes! Render Supports Docker Deployment

You can deploy both backend and frontend in **one instance** using Docker. Here's your complete setup:

---

## 📋 Render Configuration

### In Render Dashboard Settings:

1. **Service Type:** Web Service
2. **Environment:** Docker (select this!)

3. **Build & Deploy Settings:**
   - **Root Directory:** (Leave empty - uses repo root)
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Build Context Directory:** `.` (dot = root directory)
   - **Docker Command:** (Leave empty - uses Dockerfile CMD)

4. **Pre-Deploy Command:** (Leave empty - migrations run in startup)

---

## 🔧 What the Dockerfile Does

1. **Builds Frontend:**
   - Uses Node.js to compile React app
   - Creates production build

2. **Sets Up Backend:**
   - Installs Python dependencies
   - Copies Django code

3. **Configures Nginx:**
   - Serves frontend at `/` (root URL)
   - Proxies `/api/*` to Django backend
   - Proxies `/admin/*` to Django admin
   - Proxies `/health` to health check

4. **Starts Services:**
   - Runs database migrations
   - Starts Django with Gunicorn (port 8000)
   - Starts Nginx (port from Render's $PORT)

---

## ⚙️ Environment Variables

Set these in Render:

```
DATABASE_URL=<from PostgreSQL service>
CELERY_BROKER_URL=<from Redis service>
CELERY_RESULT_BACKEND=<from Redis service>
SECRET_KEY=<generate secure key>
DEBUG=False
ALLOWED_HOSTS=your-service-name.onrender.com,*.onrender.com
CORS_ALLOWED_ORIGINS=https://your-service-name.onrender.com
OPENAI_API_KEY=<your key, optional>
REACT_APP_API_URL=https://your-service-name.onrender.com/api
PORT=<auto-set by Render, don't override>
```

---

## 🚀 Deployment Steps

1. **Push Dockerfile to GitHub:**
   ```bash
   git add Dockerfile .dockerignore
   git commit -m "Add Dockerfile for single instance deployment"
   git push origin main
   ```

2. **Create Service on Render:**
   - Dashboard → "New +" → "Web Service"
   - Connect GitHub repo
   - Select "Docker" as environment

3. **Configure:**
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Build Context:** `.`
   - **Docker Command:** (empty)

4. **Add Environment Variables:**
   - Copy from list above
   - Connect PostgreSQL and Redis

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for build to complete

---

## 📍 URLs After Deployment

- **Frontend:** `https://your-service.onrender.com/`
- **API:** `https://your-service.onrender.com/api/`
- **Admin:** `https://your-service.onrender.com/admin/`
- **Health:** `https://your-service.onrender.com/health/`

All on the same domain! 🎉

---

## 🔄 Celery Worker (Separate Service)

You still need a **Background Worker** for Celery:

1. Create "Background Worker" service
2. Use same Dockerfile: `Dockerfile`
3. **Docker Command Override:**
   ```
   celery -A rcm_project worker -l info
   ```
4. Use same environment variables

---

## ✅ Advantages

- ✅ One service = simpler setup
- ✅ Same domain = no CORS issues
- ✅ Cost effective (one instance)
- ✅ Single deployment process

---

## 🐛 Troubleshooting

**Build Fails:**
- Check Dockerfile path is `Dockerfile` (root)
- Verify build context is `.` (root)

**Frontend Not Loading:**
- Check build logs for frontend build errors
- Verify Nginx is running

**API Not Working:**
- Check Django logs
- Verify proxy configuration
- Check CORS settings

**Port Issues:**
- Render sets `$PORT` automatically
- Don't override it in env vars

---

**Ready to deploy!** 🚀

