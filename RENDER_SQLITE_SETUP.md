# 🚀 Render Deployment with SQLite (Simple Setup)

## ✅ Using SQLite for Sample Project

Since this is a sample project, we'll use **SQLite** instead of PostgreSQL. This simplifies deployment - no database service needed!

---

## 📋 Render Configuration

### Service Settings:

1. **Service Type:** Web Service
2. **Environment:** Docker

### Build & Deploy Settings:

- **Root Directory:** (Leave empty)
- **Dockerfile Path:** `Dockerfile`
- **Docker Build Context Directory:** `.` (just a dot)
- **Docker Command:** (Leave empty)
- **Pre-Deploy Command:** (Leave empty)

---

## ⚙️ Environment Variables (Minimal Setup)

Since we're using SQLite, you only need:

```
SECRET_KEY=<generate a secure key>
DEBUG=False
ALLOWED_HOSTS=your-service-name.onrender.com,*.onrender.com
CORS_ALLOWED_ORIGINS=https://your-service-name.onrender.com
OPENAI_API_KEY=<your key, optional>
REACT_APP_API_URL=https://your-service-name.onrender.com/api
```

**Note:** 
- ❌ **NO** `DATABASE_URL` needed (SQLite uses file-based database)
- ❌ **NO** PostgreSQL service needed
- ⚠️ **Optional:** Redis for Celery (or skip Celery for now)

---

## 🐳 What the Dockerfile Does

1. **Builds Frontend:**
   - Compiles React app to production build

2. **Sets Up Backend:**
   - Installs Python dependencies
   - Uses SQLite (no PostgreSQL needed)
   - Copies Django code

3. **Configures Nginx:**
   - Serves frontend at `/`
   - Proxies `/api/*` to Django
   - Proxies `/admin/*` to Django admin

4. **Starts Services:**
   - Runs migrations (creates SQLite database)
   - Starts Django with Gunicorn
   - Starts Nginx

---

## 🚀 Deployment Steps

1. **Push to GitHub:**
   ```bash
   git add Dockerfile .dockerignore
   git commit -m "Add Dockerfile with SQLite support"
   git push origin main
   ```

2. **Create Service on Render:**
   - Dashboard → "New +" → "Web Service"
   - Connect GitHub repo
   - Select "Docker" environment

3. **Configure:**
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Build Context:** `.`
   - **Docker Command:** (empty)

4. **Add Environment Variables:**
   - Only the ones listed above
   - **No database connection needed!**

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for build

---

## 📍 URLs After Deployment

- **Frontend:** `https://your-service.onrender.com/`
- **API:** `https://your-service.onrender.com/api/`
- **Admin:** `https://your-service.onrender.com/admin/`

---

## ⚠️ Important Notes

### SQLite Limitations:
- ✅ Perfect for sample/demo projects
- ✅ No database service needed
- ✅ Simpler setup
- ⚠️ File-based (data persists in container)
- ⚠️ Not ideal for high-traffic production

### Celery (Optional):
- If you want async processing, create a Redis service
- Or skip Celery - processing will be synchronous
- Add `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` if using Redis

---

## 🔄 If You Need Celery Later

1. Create Redis service on Render
2. Add to environment variables:
   ```
   CELERY_BROKER_URL=<from Redis service>
   CELERY_RESULT_BACKEND=<from Redis service>
   ```
3. Create Background Worker service
4. Use same Dockerfile
5. Override Docker Command: `celery -A rcm_project worker -l info`

---

## ✅ Advantages of SQLite Setup

- ✅ **Simpler:** No database service to manage
- ✅ **Free:** No extra costs
- ✅ **Fast Setup:** Deploy in minutes
- ✅ **Perfect for Demos:** Ideal for sample projects

---

## 🐛 Troubleshooting

**Dockerfile Not Found:**
- Make sure Dockerfile is in repo root
- Check Dockerfile Path is exactly: `Dockerfile`
- Verify build context is `.` (root)

**Database Errors:**
- SQLite file is created automatically
- Check file permissions in container
- Verify migrations ran successfully

**Build Fails:**
- Check build logs for specific errors
- Verify all dependencies in requirements.txt
- Check Node.js and Python versions

---

**Ready to deploy with SQLite!** 🚀

Much simpler setup - perfect for your sample project!

