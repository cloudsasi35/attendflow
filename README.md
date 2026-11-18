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

### Backend Telemetry

The backend sends traces, metrics and logs over OTLP gRPC to the OpenTelemetry Collector (`OTEL_EXPORTER_OTLP_ENDPOINT`). The collector forwards them to Tempo, Prometheus and Loki. Setup is in [telemetry.py](backend/attendflow/telemetry.py).

| Variable | Default (compose) | Purpose |
|----------|-------------------|---------|
| `OTEL_SERVICE_NAME` | `attendflow-backend` | Service name on traces, metrics and logs |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | Collector gRPC endpoint |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | `http` | Emits stable HTTP metric names (`http_server_request_duration_seconds`, `http_route`) |
| `OTEL_SDK_DISABLED` | unset | Set to `true` to turn telemetry off |
| `LOG_LEVEL` | `INFO` | Root log level |

- `/health/live` and `/health/ready` are not traced or counted, so probe traffic does not fill dashboards.
- Each log line carries `trace_id` and `span_id` for correlation in Loki and Tempo.
- Telemetry is configured before the SQLAlchemy engine is created. Keep that order in `main.py`.
- SQLAlchemy is pinned below 2.1 because the instrumentation supports only `<2.1.0`.

Verify (with the observability stack running):

```bash
# API traces exist and no health-probe traces appear
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me >/dev/null
# Prometheus: one series per API route, no /health/* routes
docker exec attendflow-prometheus wget -qO- --post-data='query=sum by (http_route) (http_server_request_duration_seconds_count{job="attendflow-backend"})' http://localhost:9090/api/v1/query
```

Expected: Prometheus returns routes such as `/api/v1/auth/me`; no `/health/live` or `/health/ready` appears. Tempo has root spans named like `GET /api/v1/auth/me` with child `SELECT` spans.

### Frontend Telemetry

The browser sends traces to the collector through the Vite dev server. The page-load timing and each API request (XHR) become spans under the service `attendflow-frontend`. Uncaught errors and Vue component errors are recorded as spans with an exception event. Setup is in [telemetry.ts](frontend/src/telemetry.ts).

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_TELEMETRY_ENABLED` | on | Set to `false` to turn browser telemetry off. Pass it through Compose: `VITE_TELEMETRY_ENABLED=false docker compose up -d frontend` |
| `OTEL_PROXY_TARGET` | `http://otel-collector:4318` | Where the Vite `/otel` proxy forwards OTLP/HTTP requests |
| `VITE_API_URL` | `http://localhost:8000` | API origin. Trace headers (`traceparent`) are sent only to this origin |

- The browser posts to `/otel/v1/traces` on the frontend origin, so no collector CORS setting is needed.
- The exporter's own requests are excluded from tracing, so no feedback loop occurs.
- Browser metrics and logs are not collected. Only traces are.
- This is dev-only. The frontend runs under the Vite dev server, which has no production build serving the `/otel` path.
- Error messages are sent as span attributes and may contain user data. Review them before using this outside local development.
- The OpenTelemetry browser packages are pinned to the 2.7 / 0.215 release line. Newer exporter and instrumentation releases require `@opentelemetry/api` 1.10 or later, which conflicts with `@opentelemetry/sdk-trace-base` 2.x.

Verify (with the observability stack running and the frontend restarted):

```bash
# Proxy forwards OTLP: expect HTTP 200 (send an empty OTLP/JSON body, no spans)
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H 'Content-Type: application/json' -d '{}' http://localhost:5173/otel/v1/traces
```

Then open the app, sign in, and search Tempo in Grafana for service `attendflow-frontend`. Expected: `documentLoad` traces and `GET`/`POST` traces. The XHR traces also contain `attendflow-backend` spans with the same trace ID.

### Alerting

Rules are in [alerts.yml](observability/config/prometheus/rules/alerts.yml). Prometheus evaluates them and sends firing alerts to Alertmanager ([alertmanager.yml](observability/config/alertmanager/alertmanager.yml)), which routes them by severity:

| Severity | Route | Rules |
|----------|-------|-------|
| `critical` | `alert-sink /critical`, repeats hourly | `ScrapeTargetDown`, `BackendHighErrorRate`, `PostgresDown` |
| `warning` | `alert-sink /warning`, repeats every 4h | `BackendHighLatency`, `HostMemoryHigh`, `HostDiskLow`, `ContainerMemoryNearLimit`, `PostgresConnectionsHigh`, `BackendNoTraffic` |
| `none` | dropped | `Watchdog` (heartbeat that proves the pipeline works) |

The receiver is `alert-sink` ([alert_sink.py](observability/config/alert-sink/alert_sink.py)), a private container with no published port. It logs each alert as a JSON line and keeps the last 50 alerts.

View alerts:

```bash
# Prometheus rule state (firing / pending / inactive)
docker exec attendflow-prometheus wget -qO- http://localhost:9090/api/v1/alerts
# Alertmanager active alerts
docker exec attendflow-alertmanager wget -qO- http://localhost:9093/api/v2/alerts
# Delivered notifications (firing and resolved)
docker logs attendflow-alert-sink
```

To send alerts to Slack or email instead, add a receiver with credentials in a gitignored file (for example `api_url_file` for Slack), point the `critical` and `warning` routes at it, then restart Alertmanager. Do not put webhook URLs or passwords in `alertmanager.yml`.

Failure simulation (observability-only, the app is unaffected):

```bash
docker compose -f observability/docker-compose.yml stop postgres-exporter
# wait about 2 minutes, then check: ScrapeTargetDown is firing in Prometheus and reaches the sink on /critical
docker compose -f observability/docker-compose.yml start postgres-exporter
# wait about 5 minutes: the sink logs a "resolved" entry for ScrapeTargetDown
```

Expected: `ScrapeTargetDown` goes `pending` then `firing` after 2 minutes. The sink logs `critical ScrapeTargetDown firing`, then `resolved` once the exporter is back.

Rules use `for:` so one-off spikes do not page. Alertmanager reads its config only at startup. After changing it, run `docker compose -f observability/docker-compose.yml up -d --force-recreate alertmanager`.

### Failure Drills

These drills stop one dependency at a time and check what the app and the observability stack do. Run them on a local stack only. Each drill was run and the results below were observed.

**Drill 1: database outage** (application impact expected)

```bash
docker compose stop postgres
sleep 150
curl -s -o /dev/null -w "ready=%{http_code}\n" http://localhost:8000/health/ready   # expect 503
curl -s -o /dev/null -w "live=%{http_code}\n"  http://localhost:8000/health/live    # expect 200
docker exec attendflow-prometheus wget -qO- http://localhost:9090/api/v1/alerts     # PostgresDown firing
docker compose start postgres
# wait about 3 minutes: readiness returns 200 and PostgresDown resolves
```

Expected: readiness fails and liveness stays up, so the container is not restarted by the healthcheck. `PostgresDown` (critical) fires after 2 minutes and reaches the sink on `/critical`.

**Drill 2: collector outage** (application impact expected to be none)

```bash
docker compose -f observability/docker-compose.yml stop otel-collector
sleep 240
curl -s -o /dev/null -w "api=%{http_code}\n"      http://localhost:8000/health/ready   # expect 200
curl -s -o /dev/null -w "frontend=%{http_code}\n" http://localhost:5173/              # expect 200
docker exec attendflow-prometheus wget -qO- http://localhost:9090/api/v1/alerts       # ScrapeTargetDown (otel-collector) firing
docker logs --since 4m attendflow-backend 2>&1 | grep -c "Failed to export"            # expect a non-zero count
docker compose -f observability/docker-compose.yml start otel-collector
# wait about 3 minutes: ScrapeTargetDown resolves
```

Expected: the API and the frontend keep working. `ScrapeTargetDown` (critical) fires after 2 minutes, because Prometheus scrapes the collector's own metrics on `:8888`. The backend logs OTLP export failures, and the browser's `/otel` proxy returns 500 while the collector is down. The page itself is not affected. `BackendNoTraffic` (warning) fires after 15 minutes of no backend telemetry. It was observed at 15 minutes.

**Drill 3: exporter outage** — see the Failure simulation under [Alerting](#alerting).

**Where to look when something fails**

| Symptom | First check |
|---------|-------------|
| `/health/ready` returns 503 | `docker logs attendflow-backend`, then `docker compose ps postgres` |
| An alert is firing | Prometheus `api/v1/alerts`, then Alertmanager `api/v2/alerts` |
| A target is down | Prometheus `api/v1/targets`, then the container's own `docker logs` |
| Backend traces or logs are missing | `docker logs attendflow-otel-collector`, then the `BackendNoTraffic` alert |
| Browser traces are missing | Vite's `/otel` proxy returns 500 when the collector is down. Check the collector first |

Grafana (http://127.0.0.1:3000) has the same data in Explore: Prometheus for metrics, Loki for logs, and Tempo for traces.

### Observability Configuration Files

All paths are under `observability/`. Secrets live in `observability/.env` (gitignored); `.env.example` lists the variables.

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines every observability service: pinned images, healthchecks, resource limits, `restart: unless-stopped`, named volumes, and the shared `attendflow-net` and `observability-net` networks. Grafana is the only service with a host port (`127.0.0.1:3000`). |
| `.env.example` | Template for the required secrets (`GRAFANA_ADMIN_PASSWORD`, `POSTGRES_EXPORTER_PASSWORD`). Generate values with `openssl rand -hex 24`. |
| `config/otel-collector/config.yaml` | OTLP receiver on 4317/4318. Routes traces to Tempo, metrics to Prometheus (remote write) and logs to Loki. Exposes health on `:13133` and self-metrics on `:8888`. |
| `config/prometheus/prometheus.yml` | Scrape jobs for Prometheus, Alertmanager, Loki, Tempo, cAdvisor, Node Exporter, postgres-exporter and the collector. Loads the rule file. |
| `config/prometheus/rules/alerts.yml` | 10 alert rules in 5 groups. Each has a `for:` duration and a `severity` label (`critical` or `warning`). `Watchdog` is an always-firing heartbeat. |
| `config/alertmanager/alertmanager.yml` | Routes `critical` and `warning` alerts to the private `alert-sink` webhook, and `Watchdog` to a null receiver. |
| `config/alert-sink/alert_sink.py` | Small webhook receiver for Alertmanager. It prints each alert as one JSON line, read with `docker logs`. |
| `config/loki/loki.yaml` | Loki single-binary config with local filesystem storage for log chunks and the index. |
| `config/tempo/tempo.yaml` | Tempo single-binary config: OTLP ingest and local block storage. |
| `config/postgres-exporter/create-monitor-role.sql` | Creates the read-only `attendflow_monitor` role with `pg_monitor`. Idempotent, so it can be rerun after a password change. |
| `config/grafana/provisioning/datasources/datasources.yml` | Declares the Prometheus, Loki and Tempo datasources with fixed UIDs. They are read-only in the UI. |
| `config/grafana/provisioning/dashboards/dashboards.yml` | Loads dashboard JSON from `/var/lib/grafana/dashboards` into the "AttendFlow" folder. UI edits are disabled, so dashboards stay in Git. |
| `config/grafana/dashboards/*.json` | Three dashboards: Containers (cAdvisor), Host (Node Exporter) and PostgreSQL (postgres-exporter). |

Validate changes before restarting:

```bash
docker compose -f observability/docker-compose.yml config -q                       # Compose syntax
docker compose -f observability/docker-compose.yml exec prometheus promtool check config /etc/prometheus/prometheus.yml
```

Expected result: both commands exit with no errors. Prometheus and Alertmanager read their configs only at startup, so restart them after editing.

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
