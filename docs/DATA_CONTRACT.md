# DATA CONTRACT — CAT Smart Operator Assistant
## Phase 1: Data Foundation

**Version:** 1.0.0  
**Phase:** 1 — Data Foundation  
**Status:** Active  
**Last Updated:** 2026-09-24

---

> [!IMPORTANT]
> This contract governs all Phase 1 schemas.  
> **Later phases MUST NOT add new fields without updating this document.**  
> Phase 2 synthetic data MUST conform to these schemas exactly.

---

## How to Read This Document

Each field entry contains:

| Attribute | Meaning |
|---|---|
| **Source Field** | Exact column name in the company CSV |
| **Internal Field** | Snake_case database/Python name |
| **Data Type** | PostgreSQL / Python type |
| **Required** | Whether NULL is forbidden |
| **Description** | Meaning of the field |
| **Example** | A representative value |
| **References** | Foreign key relationships |
| **Data Source** | REAL COMPANY DATA or FUTURE SYNTHETIC DATA |

---

## Table 1: `telemetry`

**Purpose:** One row = one telemetry reading from a CAT machine operator session.  
**Source dataset:** Company Telemetry CSV  
**Data source classification:** 🟢 REAL COMPANY DATA

| Source Field | Internal Field | Data Type | Required | Description | Example | References | Data Source |
|---|---|---|---|---|---|---|---|
| Timestamp | `timestamp` | TIMESTAMPTZ | ✅ Yes | Date and time of the telemetry reading | `2024-01-15T08:00:00Z` | — | REAL |
| Machine ID | `machine_id` | VARCHAR(100) | ✅ Yes | Identifier for the CAT machine | `MACHINE-001` | — | REAL |
| Operator ID | `operator_id` | VARCHAR(100) | ✅ Yes | Identifier for the operator | `OP-001` | — | REAL |
| Engine Hours | `engine_hours` | FLOAT | ✅ Yes | Cumulative engine run-time in hours; must be ≥ 0 | `1234.5` | — | REAL |
| Fuel Used | `fuel_used` | FLOAT | ✅ Yes | Fuel consumed in this session (unit from source); must be ≥ 0 | `45.2` | — | REAL |
| Load Cycles | `load_cycles` | INTEGER | ✅ Yes | Number of load/dump cycles completed; must be ≥ 0 | `8` | — | REAL |
| Idling Time | `idling_time` | FLOAT | ✅ Yes | Idle duration in minutes; must be ≥ 0 | `12.0` | — | REAL |
| Seatbelt Status | `seatbelt_status` | VARCHAR(50) | ✅ Yes | Seatbelt state; accepted values: `Fastened`, `Unfastened` | `Fastened` | — | REAL |
| Safety Alert Triggered | `safety_alert_triggered` | BOOLEAN | ✅ Yes | Whether a safety alert fired during this reading | `False` | — | REAL |
| *(surrogate)* | `id` | UUID | ✅ Yes | Internal surrogate primary key (not from source CSV) | `a1b2c3...` | PK | INTERNAL |

**Constraints:**
- `engine_hours >= 0`
- `fuel_used >= 0`
- `load_cycles >= 0`
- `idling_time >= 0`
- `seatbelt_status` must be `Fastened` or `Unfastened`

**Phase 2 note:** Phase 2 synthetic data must use the exact same column names and value domains listed above.

---

## Table 2: `task_history`

**Purpose:** One row = one completed task record.  
**Source dataset:** Company Task History CSV  
**Data source classification:** 🟢 REAL COMPANY DATA

| Source Field | Internal Field | Data Type | Required | Description | Example | References | Data Source |
|---|---|---|---|---|---|---|---|
| Task ID | `task_id` | VARCHAR(100) | ✅ Yes | Business task identifier; must be unique | `TASK-001` | PK (business key) | REAL |
| Task Type | `task_type` | VARCHAR(200) | ✅ Yes | Category of work performed | `Excavation` | — | REAL |
| Weather | `weather` | VARCHAR(100) | ✅ Yes | Weather conditions during the task | `Clear` | — | REAL |
| Operator Skill | `operator_skill` | VARCHAR(100) | ✅ Yes | Operator skill level | `Intermediate` | — | REAL |
| Machine Age | `machine_age` | FLOAT | ✅ Yes | Age of the machine in years; must be ≥ 0 | `3.5` | — | REAL |
| Estimated Time | `estimated_time` | FLOAT | ✅ Yes | Planned task duration in hours; must be ≥ 0 | `4.0` | — | REAL |
| Actual Time | `actual_time` | FLOAT | ✅ Yes | Real task duration in hours; must be ≥ 0 | `4.5` | — | REAL |
| *(surrogate)* | `id` | UUID | ✅ Yes | Internal surrogate primary key | `b2c3d4...` | PK | INTERNAL |

**Constraints:**
- `task_id` UNIQUE
- `machine_age >= 0`
- `estimated_time >= 0`
- `actual_time >= 0`

> [!WARNING]
> **ML/prediction fields are FORBIDDEN here.**  
> `predicted_duration`, `confidence_interval`, and similar ML outputs belong to Phase 4 — do NOT add them to this table.

---

## Table 3: `machine_fault`

**Purpose:** One row = one machine fault event or normal-operation record.  
**Source dataset:** Phase 1 schema definition (no company CSV provided at Phase 1)  
**Data source classification:** 🟡 SCHEMA ONLY — awaiting Phase 2 synthetic data

| Source Field | Internal Field | Data Type | Required | Description | Example | References | Data Source |
|---|---|---|---|---|---|---|---|
| Task ID | `task_id` | VARCHAR(100) | ❌ Optional | Links fault to a specific task; null if unknown | `TASK-001` | FK → `task_history.task_id` | SYNTHETIC (Ph2) |
| Machine Status | `machine_status` | VARCHAR(100) | ✅ Yes | Machine state; e.g. `Operational`, `Fault`, `Maintenance`, `Offline` | `Fault` | — | SYNTHETIC (Ph2) |
| Fault Type | `fault_type` | VARCHAR(200) | ❌ Optional | Type of fault; null when machine_status is `Operational` | `Hydraulic Leak` | — | SYNTHETIC (Ph2) |
| Downtime | `downtime` | FLOAT | ✅ Yes | Minutes of machine downtime; must be ≥ 0 (0 if operational) | `30.0` | — | SYNTHETIC (Ph2) |
| *(surrogate)* | `id` | UUID | ✅ Yes | Internal surrogate primary key | `c3d4e5...` | PK | INTERNAL |

**Constraints:**
- `downtime >= 0` (CHECK constraint enforced at DB level)
- `fault_type` may be NULL when `machine_status = 'Operational'`

> [!IMPORTANT]
> Phase 1 is schema only. **Do NOT implement:**
> - Fault prediction
> - ML fault detection
> - Automatic fault inference
> - Fault severity intelligence
> - Fault diagnosis
>
> Those are Phase 3+ features.

---

## Table 4: `incident`

**Purpose:** Safety and operational incident records. Ready for Phase 3 to write into.  
**Data source classification:** 🔵 SCHEMA ONLY — Phase 3 will generate records automatically

| Source Field | Internal Field | Data Type | Required | Description | Example | References | Data Source |
|---|---|---|---|---|---|---|---|
| Incident ID | `incident_id` | UUID | ✅ Yes | Unique incident identifier (PK) | `d4e5f6...` | PK | GENERATED |
| Timestamp | `timestamp` | TIMESTAMPTZ | ✅ Yes | When the incident occurred | `2024-01-15T10:30:00Z` | — | Ph3 |
| Operator ID | `operator_id` | VARCHAR(100) | ❌ Optional | Operator involved; null if unidentified | `OP-001` | — | Ph3 |
| Machine ID | `machine_id` | VARCHAR(100) | ❌ Optional | Machine involved; null if unidentified | `MACHINE-001` | — | Ph3 |
| Event Type | `event_type` | VARCHAR(200) | ✅ Yes | Category of incident | `Seatbelt Violation` | — | Ph3 |
| Severity | `severity` | VARCHAR(50) | ✅ Yes | Severity level; accepted: `Low`, `Medium`, `High`, `Critical` | `High` | — | Ph3 |
| Description | `description` | TEXT | ❌ Optional | Free-text event description | `Operator did not fasten seatbelt.` | — | Ph3 |
| Status | `status` | VARCHAR(50) | ✅ Yes | Lifecycle state; accepted: `Open`, `Acknowledged`, `Resolved` | `Open` | — | Ph3 |

**Constraints:**
- `incident_id` UNIQUE (PK)
- `severity` ∈ {`Low`, `Medium`, `High`, `Critical`}
- `status` ∈ {`Open`, `Acknowledged`, `Resolved`}

> [!CAUTION]
> **Phase 1 does NOT automatically create incidents.**  
> Phase 3 will implement:  the seatbelt rule, weather severity adjustment, and alert generation.

---

## Table 5: `daily_task_schedule`

**Purpose:** CAT operator's scheduled daily work. Later phases will use this for "Today's Tasks" and "Current Task" UI.  
**Data source classification:** 🔵 SCHEMA ONLY — Phase 3+ will populate

| Source Field | Internal Field | Data Type | Required | Description | Example | References | Data Source |
|---|---|---|---|---|---|---|---|
| Schedule ID | `schedule_id` | UUID | ✅ Yes | Unique schedule entry identifier (PK) | `e5f6a7...` | PK | GENERATED |
| Task ID | `task_id` | VARCHAR(100) | ✅ Yes | Task being scheduled | `TASK-001` | FK → `task_history.task_id` | Ph3 |
| Operator ID | `operator_id` | VARCHAR(100) | ✅ Yes | Operator assigned | `OP-001` | — | Ph3 |
| Machine ID | `machine_id` | VARCHAR(100) | ✅ Yes | Machine assigned | `MACHINE-001` | — | Ph3 |
| Scheduled Date | `scheduled_date` | DATE | ✅ Yes | Calendar date of the task | `2024-01-15` | — | Ph3 |
| Scheduled Time | `scheduled_time` | TIME | ✅ Yes | Start time of the task | `08:00:00` | — | Ph3 |
| Task Status | `task_status` | VARCHAR(50) | ✅ Yes | Lifecycle state; accepted: `Scheduled`, `In Progress`, `Completed`, `Cancelled` | `Scheduled` | — | Ph3 |

**Constraints:**
- `schedule_id` UNIQUE (PK)
- `task_id` REFERENCES `task_history.task_id` ON DELETE RESTRICT
- `task_status` ∈ {`Scheduled`, `In Progress`, `Completed`, `Cancelled`}

---

## Relationship Summary

```
task_history (task_id PK)
    │
    ├── machine_fault.task_id    (FK, nullable, SET NULL on delete)
    └── daily_task_schedule.task_id  (FK, NOT NULL, RESTRICT on delete)
```

Telemetry and Incident reference `machine_id` and `operator_id` as plain VARCHAR
strings (not FK-constrained master tables). This is intentional for Phase 1:
- Operator and Machine master tables are NOT required at Phase 1.
- FK constraints across all tables will be evaluated in Phase 2 if a master
  table is introduced.

---

## Data Source Classification Key

| Symbol | Meaning |
|---|---|
| 🟢 REAL COMPANY DATA | Loaded from authoritative company-provided CSV |
| 🟡 SCHEMA ONLY | Schema defined; no company CSV available at Phase 1 |
| 🔵 SCHEMA ONLY | Schema defined; Phase 3+ will write records |
| INTERNAL | Not from source CSV; generated internally (UUIDs, defaults) |
| SYNTHETIC (Ph2) | Phase 2 synthetic data will populate this field |

---

## Phase 2 Synthetic Data Rules

> [!IMPORTANT]
> Phase 2 synthetic data generation MUST:
> 1. Use the exact source column names from this document.
> 2. Respect all data type and constraint rules.
> 3. NOT invent new columns without updating this contract.
> 4. NOT write ML predictions into `telemetry` or `task_history`.
> 5. NOT add fault inference logic to `machine_fault`.

---

## Change Log

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-09-24 | Initial Phase 1 schema definition |
