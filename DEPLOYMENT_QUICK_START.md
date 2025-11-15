# 🚀 Quick Deployment Guide - Render

## ✅ What's Ready

All deployment files are prepared:
- ✅ `render.yaml` - Blueprint for one-click deploy
- ✅ `backend/Procfile` - Alternative deployment method
- ✅ `backend/requirements.txt` - Includes `gunicorn` for production
- ✅ Settings configured for production environment variables

## 📝 Deployment Steps

### Method 1: One-Click Blueprint Deploy (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and create all services

3. **Configure Environment Variables:**
   After services are created, add these in each service:

   **Backend Service:**
   ```
   OPENAI_API_KEY=your_key_here (optional)
   ```

   **Frontend Service:**
   ```
   REACT_APP_API_URL=https://rcm-backend.onrender.com/api
   ```
   (Update with your actual backend URL)

4. **Run Migrations:**
   - Go to backend service → Shell
   - Run: `python manage.py migrate`
   - Run: `python manage.py createsuperuser` (optional)

### Method 2: Manual Deploy

See `RENDER_DEPLOYMENT.md` for detailed step-by-step instructions.

## 🔧 Required Environment Variables

### Backend Service
| Variable | Value | Source |
|----------|-------|--------|
| `DATABASE_URL` | Auto | From PostgreSQL service |
| `CELERY_BROKER_URL` | Auto | From Redis service |
| `CELERY_RESULT_BACKEND` | Auto | From Redis service |
| `SECRET_KEY` | Auto-generated | Render generates this |
| `DEBUG` | `False` | Set manually |
| `ALLOWED_HOSTS` | `rcm-backend.onrender.com,*.onrender.com` | Set manually |
| `CORS_ALLOWED_ORIGINS` | `https://rcm-frontend.onrender.com` | Set manually |
| `OPENAI_API_KEY` | Your key | Set manually (optional) |

### Celery Worker
| Variable | Value | Source |
|----------|-------|--------|
| `DATABASE_URL` | Same as backend | Copy from backend |
| `CELERY_BROKER_URL` | Same as backend | Copy from backend |
| `CELERY_RESULT_BACKEND` | Same as backend | Copy from backend |
| `SECRET_KEY` | Same as backend | Copy from backend |
| `DEBUG` | `False` | Set manually |
| `OPENAI_API_KEY` | Same as backend | Copy from backend |

### Frontend Service
| Variable | Value | Source |
|----------|-------|--------|
| `REACT_APP_API_URL` | `https://rcm-backend.onrender.com/api` | Set manually (update with your URL) |
| `NODE_VERSION` | `18.20.0` | Auto or set manually |

## 📋 Post-Deployment Checklist

- [ ] All services are running (green status)
- [ ] Database migrations completed
- [ ] Frontend API URL updated
- [ ] Test registration/login
- [ ] Test file upload
- [ ] Test validation results

## 🔗 Service URLs

After deployment:
- **Frontend**: `https://rcm-frontend.onrender.com`
- **Backend**: `https://rcm-backend.onrender.com`
- **Health Check**: `https://rcm-backend.onrender.com/health/`
- **Admin**: `https://rcm-backend.onrender.com/admin/`

## 💰 Estimated Cost

- PostgreSQL: $7/month
- Redis: $7/month
- Backend: Free tier or $7/month
- Celery Worker: Free tier or $7/month
- Frontend: Free

**Total**: ~$14-28/month

## 🆘 Troubleshooting

**Backend won't start:**
- Check `DATABASE_URL` is set
- Verify PostgreSQL service is running
- Check build logs for errors

**Frontend can't connect:**
- Verify `REACT_APP_API_URL` is correct
- Check CORS settings in backend
- Ensure backend is running

**Celery not processing:**
- Verify Redis connection strings
- Check worker service logs
- Ensure worker service is running

## 📚 Full Documentation

For detailed instructions, see `RENDER_DEPLOYMENT.md`

---

**Ready?** Push to GitHub and deploy! 🚀

