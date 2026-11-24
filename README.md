# AttendFlow MVP - Setup & Running Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Port 5432, 8000, 5173 available

### Start Application
```bash
cd /Users/sasi/Documents/Apps/AttendFlow
docker-compose up -d
```

### Verify Services
```bash
# Check container status
docker ps --filter "name=attendflow"

# Test backend
curl http://localhost:8000/health/live

# Access frontend
open http://localhost:5173
```

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@attendflow.local | admin123 |
| Employee | alice.kumar@attendflow.local | employee123 |
| Employee | bob.sharma@attendflow.local | employee123 |
| Employee | carol.patel@attendflow.local | employee123 |

## Architecture

### Technology Stack

**Frontend:**
- Vue 3 with Composition API + TypeScript
- Vite for bundling
- Pinia for state management
- Vue Router for navigation
- Tailwind CSS for styling
- Axios for HTTP requests

**Backend:**
- FastAPI with Uvicorn
- SQLAlchemy 2.x ORM
- PostgreSQL 15 database
- Alembic for migrations
- Pydantic for validation
- python-jose for JWT

**Infrastructure:**
- Docker Compose for orchestration
- PostgreSQL in container
- Uvicorn with hot reload (development)
- Vite dev server with HMR

### Directory Structure

```
AttendFlow/
├── frontend/                 # Vue 3 application
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── layouts/         # Layout wrappers
│   │   ├── pages/           # Page components
│   │   ├── router/          # Vue Router config
│   │   ├── services/        # API client
│   │   ├── stores/          # Pinia auth store
│   │   ├── styles/          # Tailwind CSS
│   │   ├── types/           # TypeScript types
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
│
├── backend/                  # FastAPI application
│   ├── attendflow/
│   │   ├── api/             # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── employees.py
│   │   │   ├── attendance.py
│   │   │   ├── leave.py
│   │   │   ├── dashboard.py
│   │   │   └── health.py
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── repositories.py  # Data access layer
│   │   ├── services.py      # Business logic
│   │   ├── security.py      # Auth & hashing
│   │   ├── config.py        # Settings & env
│   │   ├── database.py      # DB connection
│   │   ├── scripts.py       # Seed script
│   │   └── main.py          # FastAPI app
│   ├── tests/               # pytest test suite
│   ├── setup.py
│   ├── requirements.txt
│   ├── alembic/             # DB migrations
│   ├── .env
│   └── Dockerfile
│
├── docker-compose.yml       # Service orchestration
├── init-db.sh              # DB initialization script
└── docs/                    # Specification documents
```

## API Documentation

### Authentication

All endpoints (except `/health/*`) require Bearer token authentication.

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@attendflow.local","password":"admin123"}'
```

Response includes `access_token` to use in Authorization header:
```bash
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/auth/me
```

### Available Endpoints

**Admin Endpoints:**
- `GET /api/v1/employees` - List all employees (paginated)
- `POST /api/v1/employees` - Create new employee
- `PATCH /api/v1/employees/{id}` - Update employee
- `POST /api/v1/employees/{id}/deactivate` - Deactivate employee
- `GET /api/v1/attendance` - View all attendance records
- `GET /api/v1/attendance/today` - Today's attendance status
- `GET /api/v1/leave-requests` - View all leave requests
- `POST /api/v1/leave-requests/{id}/approve` - Approve leave
- `POST /api/v1/leave-requests/{id}/reject` - Reject leave
- `GET /api/v1/dashboard/admin` - Admin metrics dashboard
- `GET /api/v1/reports/attendance` - Attendance report (paginated)
- `GET /api/v1/reports/leave` - Leave report (paginated)
- `GET /api/v1/reports/attendance/csv` - Export attendance as CSV
- `GET /api/v1/reports/leave/csv` - Export leave as CSV

**Employee Endpoints:**
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/attendance/check-in` - Check in for work
- `POST /api/v1/attendance/check-out` - Check out from work
- `GET /api/v1/attendance/me` - View own attendance history
- `POST /api/v1/leave-requests` - Request leave
- `GET /api/v1/leave-requests/me` - View own leave requests
- `GET /api/v1/dashboard/employee` - Employee dashboard

**Health Checks:**
- `GET /health/live` - Liveness probe (always 200)
- `GET /health/ready` - Readiness probe (checks database; returns 503 when the database is unreachable)

## Database Management

### View Database

```bash
# Connect to PostgreSQL
docker exec -it attendflow-postgres psql -U attendflow -d attendflow

# List tables
\dt

# View schema
\d attendance_records
```

### Database Schema

**users**
- id (UUID, primary key)
- email (string, unique)
- password_hash (string)
- role (enum: ADMIN, EMPLOYEE)
- is_active (boolean)
- created_at, updated_at (timestamp UTC)

**employees**
- id (UUID, primary key)
- user_id (UUID, foreign key)
- employee_code (string, unique)
- full_name (string)
- department (string)
- job_title (string)
- joining_date (date)
- created_at, updated_at (timestamp UTC)

**attendance_records**
- id (UUID, primary key)
- employee_id (UUID, foreign key)
- work_date (date, in org timezone)
- check_in_at (timestamp UTC, nullable)
- check_out_at (timestamp UTC, nullable)
- status (computed: INCOMPLETE or PRESENT)
- created_at, updated_at (timestamp UTC)
- Constraint: unique(employee_id, work_date)

**leave_requests**
- id (UUID, primary key)
- employee_id (UUID, foreign key)
- leave_type (enum: CASUAL, SICK, UNPAID)
- start_date, end_date (date)
- reason (string)
- status (enum: PENDING, APPROVED, REJECTED)
- decision_note (string, nullable)
- decided_by_user_id (UUID, foreign key, nullable)
- decided_at (timestamp UTC, nullable)
- created_at, updated_at (timestamp UTC)

### Resetting Demo Data

To clear and reseed database:

```bash
# Option 1: Restart backend container (auto-seeds if SEED_DEMO_DATA=true)
docker-compose restart backend

# Option 2: Manual seed in container
docker exec attendflow-backend python -m attendflow.scripts
```

## Configuration

### Environment Variables

**.env file** (automatically loaded):
```
DATABASE_URL=postgresql://attendflow:attendflow@postgres:5432/attendflow
JWT_SECRET_KEY=dev-secret-key-change-in-production
APP_ENV=development
DEBUG=true
SEED_DEMO_DATA=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ORG_TIMEZONE=Asia/Kolkata
```

### Customization

**Change organization timezone:**
- Update `ORG_TIMEZONE` in docker-compose.yml environment
- Restart backend: `docker-compose restart backend`
- Affects: work_date calculation, displayed times

**Change demo seed data:**
- Edit `backend/attendflow/scripts.py`
- Restart backend to reseed: `docker-compose restart backend`

**Change JWT expiration:**
- Edit `backend/attendflow/security.py`, `TOKEN_EXPIRE_MINUTES` constant
- Restart backend

## Logs & Debugging

### View Logs

```bash
# Backend logs (including SQL queries with DEBUG=true)
docker logs attendflow-backend -f

# Frontend logs
docker logs attendflow-frontend -f

# Database logs
docker logs attendflow-postgres -f
```

### Debug Mode

Backend runs with `DEBUG=true`. SQL queries are logged to console.

Frontend Vite dev server has HMR enabled - changes to `.vue` or `.ts` files trigger hot reload.

### Common Issues

**Frontend showing blank page:**
- Ensure backend is running: `curl http://localhost:8000/health/live`
- Check console for errors (F12)
- Vite may take 30 seconds to start on first run

**"Cannot GET /api/v1/..." errors:**
- Ensure backend container is running
- Check backend logs: `docker logs attendflow-backend`
- Verify CORS is configured: `CORS_ORIGINS` includes frontend URL

**Database connection failed:**
- Ensure postgres container is healthy: `docker ps | grep postgres`
- Check DATABASE_URL in .env matches container
- Restart database: `docker-compose restart postgres`

**Enum comparison errors:**
- Already fixed in services.py (v2.1+)
- If still occurring, ensure backend restarted: `docker-compose restart backend`

## Testing

Frontend tests are written using Vitest but not yet configured to run in Docker.

Backend pytest suite is available in `backend/tests/` but pytest must be installed separately (not in Docker image by default).

To run backend tests locally:
```bash
cd backend
python -m pytest tests/ -v
```

## Deployment

For production deployment to Rancher:

1. Update `.env` with production values:
   - `JWT_SECRET_KEY`: Generate secure random key
   - `DATABASE_URL`: Point to production PostgreSQL
   - `CORS_ORIGINS`: Set to production frontend domain
   - `APP_ENV`: Change to "production"

2. Build Docker images:
   ```bash
   docker-compose build
   ```

3. Push to registry:
   ```bash
   docker tag attendflow-backend:latest registry.example.com/attendflow-backend:v1.0.0
   docker push registry.example.com/attendflow-backend:v1.0.0
   # Repeat for frontend image
   ```

4. Deploy to Rancher using docker-compose or Kubernetes manifests

## Known Limitations

See [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md) for detailed list.

Short summary:
- No refresh token (session lost on F5 refresh)
- No file uploads (profile pictures, documents)
- No email notifications
- No role modifications (can't change user role after creation)
- Demo data includes predictable test attendance/leave
- No bulk employee import

## Support & Documentation

- **Product Requirements**: See `docs/01-product-requirements.md`
- **Architecture**: See `docs/02-application-architecture.md`
- **Database Design**: See `docs/03-database-design.md`
- **UI/UX Guidelines**: See `docs/04-ui-ux-guidelines.md`
- **Development Guidelines**: See `docs/05-development-guidelines.md`
- **Testing**: See `docs/06-testing-acceptance-criteria.md`
- **Deployment**: See `docs/07-deployment-requirements.md`
- **Decisions**: See `DECISIONS.md` for implementation choices
- **Progress**: See `PROGRESS.md` for development timeline

## Next Steps (Beyond MVP)

1. Implement refresh tokens for persistent sessions
2. Add email notifications for leave approvals
3. Build employee self-service profile/password management
4. Add attendance summary reports by department
5. Implement shift management (different work hours per role)
6. Add attendance reconciliation for corrections
7. Integrate with calendar systems (sync holidays)
8. Add mobile app support
9. Implement audit logging
10. Add performance dashboards (by department, manager)
