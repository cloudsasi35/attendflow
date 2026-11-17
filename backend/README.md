# AttendFlow Backend

FastAPI-based backend for Employee Attendance & Leave Management.

## Setup

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Database

```bash
alembic upgrade head  # Apply migrations
python -m attendflow.scripts.seed  # Seed demo data
```

## Run

```bash
uvicorn attendflow.main:app --reload
```

API docs: http://localhost:8000/docs
