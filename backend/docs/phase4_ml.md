# Phase 4 ML Intelligence & Task-Time Prediction

## 1. Objective
Build an explainable Machine Learning system that predicts **Task Duration** (`actual_time`) before or at the start of a task, without leaking future telemetry or incident data.

## 2. Target Variable
**`actual_time`** (from `task_history` table) representing the total hours to complete a task.

## 3. Input Tables
- `task_history`: Core task data (estimated time, weather, skill, machine age).
- `daily_task_schedule`: Chronological ordering (date/time) and Operator/Machine mapping.
- `incident`: Historical operator risk records (from Phase 3).
- `machine_fault`: Historical machine reliability records (from Phase 2).

## 4. Feature Definitions
**Numerical Features:**
- `estimated_time` (Planned duration)
- `machine_age` (Years)
- `operator_historical_avg_time` (Historical average of actual_time)
- `operator_historical_incident_count` (Total Phase 3 incidents)
- `machine_historical_fault_count` (Total machine faults)

**Categorical Features:**
- `task_type`
- `weather`
- `operator_skill`
- `operator_id`
- `machine_id`

## 5. Historical Feature Logic & Leakage Prevention
To prevent **Data Leakage**, current/future task features cannot be used. 
For every task $T_i$:
- `operator_historical_avg_time` is the mean of `actual_time` for tasks $T_k$ where $T_k < T_i$.
- `operator_historical_incident_count` counts incidents strictly occurring before $T_i$.
- `machine_historical_fault_count` counts faults strictly occurring before $T_i$.

Current-task `telemetry` (idle time, load cycles) and current-task `machine_fault` downtime are strictly excluded because they represent information generated *during* or *after* the task, which is unavailable at prediction time.

## 6. Chronological Split
Data is sorted by `scheduled_date` and `scheduled_time`. The first 80% is used for **Training**, and the final 20% is used for **Testing**. Random shuffling across the temporal boundary is explicitly prohibited.

## 7. Models Evaluated
1. **Business Baseline**: Predicts the `estimated_time` provided by the company.
2. **Linear Regression**: A standard statistical baseline model.
3. **Random Forest Regressor**: A non-linear tree-based model to capture complex interactions (e.g., Operator Skill + Weather + Machine Age).

## 8. Metrics
Models are evaluated on:
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **R²** (Coefficient of Determination)

## 9. Model Artifact
The final `RandomForestRegressor` and its `ColumnTransformer` preprocessing pipeline are saved using `joblib` at `model_artifacts/task_duration_model.joblib`. This ensures exact matching of One-Hot Encoded features during inference.

## 10. Inference Process
The `TaskPredictionService` loads the saved artifact, accepts a dictionary of static context and pre-computed historical features, and transforms the data using the saved pipeline to output a numeric duration estimate in hours, along with the top global features influencing the tree.

## 11. Known Limitations
- If an operator has no historical tasks (e.g., a new operator), the pipeline assigns the median training value. This may reduce accuracy for new operators.
- The dataset (176 tasks) is extremely small for advanced Machine Learning. Tree-based models can easily overfit such data, making the Baseline (`estimated_time`) highly competitive. Deep learning approaches were intentionally excluded due to lack of sample volume.
