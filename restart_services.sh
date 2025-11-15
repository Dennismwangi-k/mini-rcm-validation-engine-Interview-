#!/bin/bash
echo "🛑 Stopping existing services..."
pkill -f "manage.py runserver" 2>/dev/null
pkill -f "celery.*worker" 2>/dev/null
sleep 2

echo "🚀 Starting backend server..."
cd backend
python3 manage.py runserver > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

echo "🚀 Starting Celery worker..."
celery -A rcm_project worker --loglevel=info > ../celery.log 2>&1 &
CELERY_PID=$!
echo "Celery PID: $CELERY_PID"

sleep 3
echo ""
echo "✅ Services restarted!"
echo "📝 Backend log: backend.log"
echo "📝 Celery log: celery.log"
echo ""
echo "To stop services, run:"
echo "  kill $BACKEND_PID $CELERY_PID"
