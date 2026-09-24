"""
Dataset construction and leakage-safe feature engineering.
"""
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Tuple

from sqlalchemy.orm import Session
from app.models.task_history import TaskHistory
from app.models.daily_task import DailyTaskSchedule
from app.models.machine_fault import MachineFault
from app.models.incident import Incident

def build_dataset(db: Session) -> pd.DataFrame:
    """
    Constructs the leakage-safe chronological ML dataset from the PostgreSQL database.
    """
    # 1. Load Data
    tasks_query = db.query(TaskHistory).all()
    schedules_query = db.query(DailyTaskSchedule).all()
    faults_query = db.query(MachineFault).all()
    incidents_query = db.query(Incident).all()

    # Convert to DataFrames
    tasks_df = pd.DataFrame([{
        "task_id": t.task_id,
        "machine_id": t.machine_id,
        "operator_id": t.operator_id,
        "actual_time": t.actual_time,
        "estimated_time": t.estimated_time,
        "task_type": t.task_type,
        "weather": t.weather,
        "operator_skill": t.operator_skill,
        "machine_age": t.machine_age
    } for t in tasks_query])
    
    schedules_df = pd.DataFrame([{
        "task_id": s.task_id,
        "scheduled_date": s.scheduled_date,
        "scheduled_time": s.scheduled_time
    } for s in schedules_query])
    
    # Faults linked to tasks
    faults_df = pd.DataFrame([{
        "task_id": f.task_id,
        "machine_status": f.machine_status
    } for f in faults_query if f.machine_status != 'NORMAL'])
    
    # Incidents linked to operator and time
    incidents_df = pd.DataFrame([{
        "operator_id": i.operator_id,
        "timestamp": i.timestamp
    } for i in incidents_query])
    
    if tasks_df.empty or schedules_df.empty:
        return pd.DataFrame()

    # 2. Join Core Data
    df = pd.merge(tasks_df, schedules_df, on="task_id", how="inner")
    
    # Combine date and time to create a proper chronological timestamp
    df['task_datetime'] = pd.to_datetime(
        df['scheduled_date'].astype(str) + ' ' + df['scheduled_time'].astype(str)
    )
    
    # Ensure incidents timestamp is tz-naive or matched for comparison
    if not incidents_df.empty:
        incidents_df['timestamp'] = pd.to_datetime(incidents_df['timestamp']).dt.tz_localize(None)
    
    # 3. Chronological Sort
    df = df.sort_values(by="task_datetime").reset_index(drop=True)
    
    # 4. Feature Engineering (Strict Leakage Prevention)
    # We iterate chronologically and build features using only data BEFORE current row
    
    # State tracking
    operator_task_times = {} # operator_id -> list of actual_times
    operator_incident_counts = {} # operator_id -> total incident count up to this point
    machine_fault_counts = {} # machine_id -> total faults up to this point
    
    # We will map faults to exactly when they occurred (by task_datetime)
    # So we join faults to their task_datetime first
    if not faults_df.empty:
        faults_timed = pd.merge(faults_df, df[['task_id', 'task_datetime']], on='task_id', how='inner')
    else:
        faults_timed = pd.DataFrame(columns=['machine_id', 'task_datetime'])
        
    operator_historical_avg = []
    operator_hist_incidents = []
    machine_hist_faults = []
    
    for idx, row in df.iterrows():
        op = row['operator_id']
        mac = row['machine_id']
        t_time = row['task_datetime']
        
        # A. Operator Historical Average Time (strictly before T)
        if op in operator_task_times and len(operator_task_times[op]) > 0:
            operator_historical_avg.append(np.mean(operator_task_times[op]))
        else:
            operator_historical_avg.append(np.nan) # Fallback handled in pipeline
            
        # B. Operator Historical Incident Count (strictly before T)
        if not incidents_df.empty:
            # Count incidents for this operator where timestamp < t_time
            inc_count = len(incidents_df[(incidents_df['operator_id'] == op) & (incidents_df['timestamp'] < t_time)])
        else:
            inc_count = 0
        operator_hist_incidents.append(inc_count)
        
        # C. Machine Historical Fault Count (strictly before T)
        if not faults_timed.empty:
            f_count = len(faults_timed[(faults_timed['task_datetime'] < t_time)]) 
            # Wait, faults are per machine. I need machine_id for faults.
            # But faults_timed doesn't have machine_id directly unless I join it.
            # Let's fix that below: we just need to join machine_id from schedules to faults.
            pass
            
        # After calculation, we add current task's result to state for FUTURE rows
        if op not in operator_task_times:
            operator_task_times[op] = []
        operator_task_times[op].append(row['actual_time'])
        
    df['operator_historical_avg_time'] = operator_historical_avg
    df['operator_historical_incident_count'] = operator_hist_incidents
    
    # Fix Machine Fault mapping
    machine_hist_faults = []
    if not faults_df.empty:
        faults_with_mac = pd.merge(faults_df, df[['task_id', 'machine_id', 'task_datetime']], on='task_id', how='inner')
    else:
        faults_with_mac = pd.DataFrame(columns=['task_id', 'machine_id', 'task_datetime'])

    for idx, row in df.iterrows():
        mac = row['machine_id']
        t_time = row['task_datetime']
        
        if not faults_with_mac.empty:
            f_count = len(faults_with_mac[(faults_with_mac['machine_id'] == mac) & (faults_with_mac['task_datetime'] < t_time)])
        else:
            f_count = 0
        machine_hist_faults.append(f_count)
        
    df['machine_historical_fault_count'] = machine_hist_faults
    
    return df

def get_train_test_split(df: pd.DataFrame, train_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits data chronologically. Assumes df is already sorted by task_datetime.
    """
    n_total = len(df)
    n_train = int(n_total * train_ratio)
    
    if n_total == 0:
        return df, df
        
    train_df = df.iloc[:n_train].copy()
    test_df = df.iloc[n_train:].copy()
    
    # Verification
    if not train_df.empty and not test_df.empty:
        train_end = train_df.iloc[-1]['task_datetime']
        test_start = test_df.iloc[0]['task_datetime']
        if train_end > test_start:
            raise ValueError("Chronological split failed: Train end is after Test start.")
            
    return train_df, test_df
