# Phase 2 Synthetic Data Generation

## Overview
This document describes the Phase 2 Synthetic Data Generation system for the CAT Smart Operator Assistant. Since real operator data is not always available, this generator populates the database with statistically realistic data to support Phase 3 (Rules) and Phase 4 (Machine Learning).

## Constraints
- The generator **does not** create safety incidents. It generates raw telemetry (including unfastened seatbelts and alerts) which later phases process.
- The generator is **deterministic**. Running with `--seed 42` will always produce the exact same IDs, rows, and values.
- Deleting the generated data via `--reset` uses an explicit reverse-FK order to ensure the database schema and Alembic versions are never corrupted.

## Usage
To generate 30 days of data, run:
```powershell
python backend/scripts/generate_synthetic_data.py --seed 42 --reset
```

## Profiles

### Operators & Anomalies
Operators are configured with explicit baselines. Selected operators have anomalies deliberately injected so Phase 4 models have a ground truth to detect.

- **OP1001, OP1002, OP1005**: Normal baseline behaviors.
- **OP1003**: Deliberately exhibits a *High Idling* anomaly in ~25% of sessions.
- **OP1004**: Deliberately exhibits an *Unusual Load Cycles* anomaly in ~25% of sessions.

### Machines
- **EXC001, EXC002, EXC003**: Excavators of varying ages.
- **LDR001, LDR002**: Loaders of varying ages.

### Causal Dependencies
The generator explicitly links downtime to task delays. If a `MachineFault` occurs and generates downtime (e.g., 30 minutes for an Engine Fault), the `actual_time` of the associated `TaskHistory` is increased proportionally over its `estimated_time`.
