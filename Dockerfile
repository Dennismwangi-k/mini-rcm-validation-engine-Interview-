# Multi-stage build for combined backend + frontend deployment
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build frontend (API URL is determined at runtime based on hostname)
# No need to set REACT_APP_API_URL - it will use relative /api in production
RUN npm run build

# Production stage - Python backend with built frontend
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (PostgreSQL client for database connections)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/build /app/staticfiles/frontend

# Create nginx config template
RUN echo 'server { \
    listen PORT_PLACEHOLDER; \
    server_name _; \
    \
    # Serve frontend static files \
    location / { \
        root /app/staticfiles/frontend; \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Proxy API requests to Django \
    location /api { \
        proxy_pass http://127.0.0.1:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # Proxy admin panel \
    location /admin { \
        proxy_pass http://127.0.0.1:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # Proxy health check \
    location /health { \
        proxy_pass http://127.0.0.1:8000; \
        proxy_set_header Host $host; \
    } \
}' > /etc/nginx/sites-available/default.template

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Get PORT from environment (Render provides this)\n\
PORT=${PORT:-8080}\n\
\n\
# Replace PORT_PLACEHOLDER in nginx config\n\
sed "s/PORT_PLACEHOLDER/$PORT/g" /etc/nginx/sites-available/default.template > /etc/nginx/sites-available/default\n\
\n\
# Run migrations\n\
python manage.py migrate --noinput\n\
\n\
# Collect static files\n\
python manage.py collectstatic --noinput\n\
\n\
# Start Django in background\n\
gunicorn rcm_project.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120 &\n\
\n\
# Start nginx in foreground\n\
nginx -g "daemon off;"' > /app/start.sh && chmod +x /app/start.sh

# Expose port (Render uses $PORT environment variable)
EXPOSE 8080

# Start script
CMD ["/app/start.sh"]

