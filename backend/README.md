# CAT Smart Operator Assistant — Phase 1: Data Foundation

## Overview

This is the **Phase 1 Data Foundation** for the CAT Smart Operator Assistant — a backend built with:

| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| DB Driver | psycopg2-binary |

---

## Project Structure

```
caterpillar/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI application
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic-settings (reads from env)
│   │   │   └── database.py       # Engine, session, Base, get_db()
│   │   ├── models/
│   │   │   ├── telemetry.py      # Telemetry ORM model
│   │   │   ├── task_history.py   # TaskHistory ORM model
│   │   │   ├── machine_fault.py  # MachineFault ORM model
│   │   │   ├── incident.py       # Incident ORM model
│   │   │   └── daily_task.py     # DailyTaskSchedule ORM model
│   │   ├── schemas/
│   │   │   ├── telemetry.py      # Pydantic v2 telemetry schemas
│   │   │   ├── task_history.py   # Pydantic v2 task history schemas
│   │   │   ├── machine_fault.py  # Pydantic v2 machine fault schemas
│   │   │   ├── incident.py       # Pydantic v2 incident schemas
│   │   │   └── daily_task.py     # Pydantic v2 daily task schemas
│   │   └── ingestion/
│   │       └── loader.py         # CSV ingestion pipeline
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_phase1_schema.py
│   ├── tests/
│   │   ├── conftest.py           # Shared pytest fixtures
│   │   ├── test_models.py        # ORM + schema tests
│   │   ├── test_ingestion.py     # Ingestion pipeline tests
│   │   └── test_api.py           # FastAPI /health tests
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                      # ← update with real credentials
├── docs/
│   └── DATA_CONTRACT.md          # Authoritative field contract
└── CAT_Operator_Intelligence_Research_Brief.md
```

---

## Setup

### 1. Create and activate the virtual environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database

Alembic manages **tables**, not the database itself.  
Create the database manually first:

```sql
-- In psql or pgAdmin:
CREATE DATABASE cat_operator_assistant;
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update with your credentials:

```powershell
copy .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql+psycopg2://<username>:<password>@localhost:5432/cat_operator_assistant
APP_ENV=development
LOG_LEVEL=INFO
```

### 5. Run Alembic migrations

```powershell
alembic upgrade head
```

This creates all 5 Phase 1 tables:
- `telemetry`
- `task_history`
- `machine_fault`
- `incident`
- `daily_task_schedule`

### 6. Start the FastAPI server

```powershell
uvicorn app.main:app --reload
```

Visit [http://localhost:8000/health](http://localhost:8000/health) to verify.

---

## Running Tests

Tests use an **in-memory SQLite** database by default (no PostgreSQL needed):

```powershell
pytest -v
```

To run against a real PostgreSQL instance:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg2://postgres:password@localhost:5432/cat_operator_assistant_test"
pytest -v
```

---

## Loading Company CSV Data

Place your company CSV files in the project root (next to `backend/`):
- `telemetry.csv` (or `Telemetry.csv`)
- `task_history.csv` (or `TaskHistory.csv`)

Then use the ingestion loader:

```python
from app.core.database import SessionLocal
from app.ingestion.loader import load_telemetry_csv, load_task_history_csv

with SessionLocal() as db:
    result = load_telemetry_csv("../telemetry.csv", db)
    print(f"Inserted: {result.rows_inserted}, Errors: {len(result.errors)}")
```

---

## Environment Variables Reference

| Variable | Required | Example | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ Yes | `postgresql+psycopg2://user:pass@localhost:5432/cat_operator_assistant` | PostgreSQL connection string |
| `APP_ENV` | ❌ No | `development` | Application environment |
| `LOG_LEVEL` | ❌ No | `INFO` | Python logging level |

---

## Data Contract

See [`docs/DATA_CONTRACT.md`](../docs/DATA_CONTRACT.md) for the authoritative field-by-field schema documentation.

---

## Phase Scope

**Phase 1 implements the Data Foundation ONLY.**

The following are deliberately out of scope for Phase 1:

- ❌ Synthetic data generation
- ❌ Safety rules / severity logic
- ❌ Alert queueing / incident generation
- ❌ Anomaly detection / ML
- ❌ Task duration regression
- ❌ Dashboard / UI
- ❌ LLM / TTS
- ❌ Proximity detection
