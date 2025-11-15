# 🐘 Render PostgreSQL Database Setup

## ✅ Using Render PostgreSQL Database

Your PostgreSQL database is now configured! Here's how to set it up:

---

## 🔗 Your Database Connection String

```
postgresql://pylap:1ZW8FW3FFG1MRY8yYLS2jkSaWuTaxGI9@dpg-d4cfuu7diees7393cjv0-a.oregon-postgres.render.com/pylap_yecr
```

---

## ⚙️ Render Environment Variables

### In Your Web Service Settings:

Add this environment variable:

```
DATABASE_URL=postgresql://pylap:1ZW8FW3FFG1MRY8yYLS2jkSaWuTaxGI9@dpg-d4cfuu7diees7393cjv0-a.oregon-postgres.render.com/pylap_yecr
```

### Complete Environment Variables List:

```
DATABASE_URL=postgresql://pylap:1ZW8FW3FFG1MRY8yYLS2jkSaWuTaxGI9@dpg-d4cfuu7diees7393cjv0-a.oregon-postgres.render.com/pylap_yecr
SECRET_KEY=<generate a secure key>
DEBUG=False
ALLOWED_HOSTS=your-service-name.onrender.com,*.onrender.com
CORS_ALLOWED_ORIGINS=https://your-service-name.onrender.com
OPENAI_API_KEY=<optional>
```

**Note:** If you want to add Celery with Redis later, you can add:
```
CELERY_BROKER_URL=<from Redis service>
CELERY_RESULT_BACKEND=<from Redis service>
```

---

## 🚀 What Changed

1. **Dockerfile:**
   - Added `postgresql-client` back (needed for database connections)

2. **Settings:**
   - Already configured to use PostgreSQL when `DATABASE_URL` is set
   - Falls back to SQLite if `DATABASE_URL` is not provided

3. **Requirements:**
   - Already has `psycopg2-binary` and `dj-database-url` installed

---

## 📋 Deployment Steps

1. **Push Updated Code:**
   ```bash
   git add Dockerfile backend/rcm_project/settings.py
   git commit -m "Add PostgreSQL support with Render database"
   git push origin main
   ```

2. **In Render Dashboard:**
   - Go to your Web Service → Settings → Environment
   - Add `DATABASE_URL` with your connection string (see above)
   - Save and redeploy

3. **Run Migrations:**
   - Go to your service → Shell
   - Run: `python manage.py migrate`
   - (Optional) Run: `python manage.py createsuperuser`

---

## ✅ Advantages of PostgreSQL

- ✅ **Persistent Data:** Data survives container restarts
- ✅ **Production Ready:** Better for production workloads
- ✅ **Better Performance:** Optimized for concurrent access
- ✅ **Full Features:** All PostgreSQL features available

---

## 🔄 Local Development

For local development, you can:

1. **Use PostgreSQL:**
   - Set `DATABASE_URL` in your local `.env` file
   - Or use the Render database (if accessible)

2. **Use SQLite:**
   - Don't set `DATABASE_URL`
   - It will automatically use SQLite

---

## 🐛 Troubleshooting

**Connection Errors:**
- Verify `DATABASE_URL` is set correctly
- Check database is running on Render
- Ensure connection string format is correct

**Migration Errors:**
- Run migrations in Shell: `python manage.py migrate`
- Check database permissions
- Verify connection string credentials

---

**Ready to use PostgreSQL!** 🐘

