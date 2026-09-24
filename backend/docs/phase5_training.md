# Phase 5: Operator Training Hub

## Overview
Phase 5 implements the closed-loop intelligence architecture where Phase 3 anomalies deterministically trigger targeted operator training.

## Database Additions
Additive tables (no changes to Phase 1-4 schemas):
- `training_module`: Core learning content (e.g., "Seatbelt Safety Fundamentals").
- `training_question`: Multiple-choice questions for each module.
- `operator_training_progress`: Summary table of an operator's module status and best score.
- `operator_training_attempt`: Append-only log storing every quiz attempt chronologically, ensuring retries do not destructively overwrite past scores.

## Backend Architecture
- **Shared Session**: The Training Hub utilizes the exact same `app.core.database.get_db` and `app.core.config.settings` structures as the rest of the application.
- **Server-Side Grading**: The `GET /modules/{id}` endpoint exclusively transmits the question text and options to the frontend. The `correct_answer` and `explanation` remain strictly server-side. The frontend submits a `QuizSubmission` map via POST, and the server computes the score, atomicially updating both `attempt` and `progress` rows in a single transaction.

## Dashboard Integration
To fulfill the requirement that the Training Hub serves as a cohesive extension of the Operator Dashboard (despite the absence of a preexisting frontend codebase in Phases 1-4), a lightweight React shell was constructed in `/frontend`.

This dashboard fetches **real** production data via the `/api/dashboard/{operator_id}` route:
- **Current Task**: Queried directly from `daily_task_schedule`.
- **Machine Status**: Queried directly from `machine_fault`.
- **Safety Status**: Queried directly from `incident` (Phase 3).
- **Training Recommendation**: If `incident` detects a seatbelt violation, a `Seatbelt Safety` recommendation is prominently rendered.

## Verification
- Run `pytest tests/ -v` to ensure backend integrity.
- Run `cd frontend && npm run dev` to launch the Operator UI.
- Run `uvicorn app.main:app --reload` to launch the API.
