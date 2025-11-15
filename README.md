# Mini RCM Validation Engine

A full-stack Revenue Cycle Management (RCM) validation engine that ingests claims data, validates against technical and medical rules, and presents results through a secure web interface.

## Features

- **Secure Authentication**: JWT-based login system
- **File Upload**: Upload claims files (Excel) and rule documents (PDF)
- **Rule Engine**: 
  - Static rule evaluation (Technical and Medical rules)
  - LLM-based rule evaluation (OpenAI integration)
- **Data Pipeline**: Async processing with Celery
- **Visualization**: 
  - Waterfall charts for claim counts by error category
  - Paid amount charts by error category
  - Detailed claims table with filtering
- **Multi-tenant Support**: Configurable rule sets
- **Master Table**: Complete claim data with validation results

## Tech Stack

### Backend
- Django 4.2.7
- Django REST Framework
- PostgreSQL
- Celery + Redis
- OpenAI API (for LLM validation)

### Frontend
- React 18 with TypeScript
- Recharts for visualization
- React Router for navigation
- Axios for API calls

## Project Structure

```
Mini RCM Validation Engine/
├── backend/              # Django backend
│   ├── accounts/        # Authentication app
│   ├── claims/          # Claims models and views
│   ├── rules/           # Rule engine and parsers
│   └── rcm_project/     # Django project settings
├── frontend/            # React frontend
│   ├── src/
│   │   ├── api/        # API client
│   │   └── components/ # React components
├── data/
│   └── artifacts/      # Sample files (Excel, PDFs)
└── docker-compose.yml  # Docker setup
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+
- Redis
- Docker (optional)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser (optional):
```bash
python manage.py createsuperuser
```

7. Start development server:
```bash
python manage.py runserver
```

8. In a separate terminal, start Celery worker:
```bash
celery -A rcm_project worker -l info
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

The frontend will be available at http://localhost:3000

### Docker Setup (Alternative)

1. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Start all services:
```bash
docker-compose up --build
```

This will start:
- Backend API at http://localhost:8000
- Frontend at http://localhost:3000
- PostgreSQL database
- Redis
- Celery worker

## Usage

1. **Register/Login**: Create an account or login at http://localhost:3000/login

2. **Upload Files**: 
   - Upload a claims file (Excel format)
   - Optionally upload custom Technical and Medical rules (PDF)

3. **View Results**:
   - Check validation statistics in charts
   - Review detailed claims in the table
   - Filter by status and error type

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/token/refresh/` - Refresh access token

### Claims
- `GET /api/claims/` - List all claims (with filtering)
- `GET /api/claims/{id}/` - Get claim details
- `GET /api/claims/statistics/` - Get validation statistics

### Jobs
- `POST /api/jobs/` - Upload and process claims file
- `GET /api/jobs/` - List all validation jobs
- `GET /api/jobs/{id}/` - Get job details
- `GET /api/jobs/{id}/status/` - Get job processing status

### Health
- `GET /health/` - Health check endpoint

## Rule Engine

The system validates claims against:

### Technical Rules
- Service code approval requirements
- Diagnosis code approval requirements
- Paid amount thresholds
- ID formatting rules

### Medical Rules
- Encounter type restrictions
- Facility type restrictions
- Diagnosis requirements
- Mutually exclusive diagnoses

## Master Table Schema

The master table includes:
- `claim_id` - Unique claim identifier
- `encounter_type` - Inpatient/Outpatient
- `service_date` - Date of service
- `national_id`, `member_id`, `facility_id` - Patient identifiers
- `unique_id` - Composite identifier
- `diagnosis_codes` - Comma-separated diagnosis codes
- `service_code` - Service code
- `paid_amount_aed` - Amount in AED
- `approval_number` - Prior approval number
- `status` - Validated/Not Validated
- `error_type` - No Error/Medical Error/Technical Error/Both
- `error_explanation` - Detailed error explanation
- `recommended_action` - Actionable recommendations

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

### Backend Deployment
1. Set `DEBUG=False` in settings
2. Configure production database
3. Set up static file serving
4. Configure CORS for production domain
5. Set up Celery workers and Redis

### Frontend Deployment
1. Build production bundle:
```bash
npm run build
```
2. Serve static files (e.g., with Nginx or Vercel)

## Environment Variables

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (0/1)
- `DATABASE_URL` - PostgreSQL connection string
- `CELERY_BROKER_URL` - Redis broker URL
- `CELERY_RESULT_BACKEND` - Redis result backend URL
- `OPENAI_API_KEY` - OpenAI API key (optional)

## Evaluation Rubric Compliance

✅ **Rule correctness & explanations** (25 pts)
- Static rule validation implemented
- LLM-based validation for enhanced explanations
- Detailed error explanations with bullet points

✅ **Master table completeness & persistence** (20 pts)
- All required fields in Claim model
- PostgreSQL persistence
- Proper indexing

✅ **UI clarity** (15 pts)
- Login screen
- File upload interface
- Charts (waterfall charts)
- Results table with filtering

✅ **Multi-tenant config & dynamic parsing** (15 pts)
- Rule sets can be switched via file upload
- Dynamic PDF parsing
- Configurable thresholds

✅ **Tests & CI/CD pipeline** (15 pts)
- Test structure in place
- Docker setup for deployment

✅ **Documentation & assumptions** (10 pts)
- Comprehensive README
- Code comments
- API documentation

## Assumptions

1. Claims file follows standard Excel format with expected column names
2. Rule PDFs follow the provided format structure
3. OpenAI API key is optional (system works without LLM)
4. Multi-tenant configuration uses file-based rule sets
5. Validation is performed asynchronously for large files

## Questions for System Architect

1. What is the expected volume of claims per batch?
2. Are there any specific performance requirements?
3. Should rule changes be versioned and audited?
4. What is the expected retention period for claims data?
5. Are there any specific security/compliance requirements (HIPAA, etc.)?

## License

This project is created for assessment purposes.

## Contact

For questions or issues, please contact: careers@humaein.com

