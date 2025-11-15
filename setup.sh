#!/bin/bash

echo "Setting up Mini RCM Validation Engine..."

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update it with your settings."
fi

# Run migrations
python manage.py migrate

echo "Backend setup complete!"

# Frontend setup
echo "Setting up frontend..."
cd ../frontend
npm install

echo "Frontend setup complete!"

echo ""
echo "Setup complete! Next steps:"
echo "1. Update backend/.env with your settings"
echo "2. Start PostgreSQL and Redis"
echo "3. Run 'cd backend && source venv/bin/activate && python manage.py runserver'"
echo "4. In another terminal, run 'cd backend && source venv/bin/activate && celery -A rcm_project worker -l info'"
echo "5. In another terminal, run 'cd frontend && npm start'"
echo ""
echo "Or use Docker: docker-compose up --build"

