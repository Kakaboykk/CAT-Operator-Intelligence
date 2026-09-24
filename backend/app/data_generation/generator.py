"""
Core generation engine for Phase 2 Synthetic Data.
"""
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Tuple

from app.models.daily_task import DailyTaskSchedule
from app.models.machine_fault import MachineFault
from app.models.task_history import TaskHistory
from app.models.telemetry import Telemetry
from app.data_generation.config import (
    FAULTS,
    MACHINES,
    OPERATORS,
    TASKS,
    WEATHER_CONDITIONS,
    WEATHER_PROBABILITIES,
)


class SyntheticDataGenerator:
    def __init__(self, seed: int, days: int = 30):
        self.seed = seed
        self.days = days
        random.seed(self.seed)

        # Counter for deterministic UUID generation
        self._uuid_counter = 0

        # State tracking
        self.engine_hours: Dict[str, float] = {m.machine_id: random.uniform(500, 5000) for m in MACHINES}
        
        # Output collections (in FK-safe generation order)
        self.task_histories: List[TaskHistory] = []
        self.machine_faults: List[MachineFault] = []
        self.daily_schedules: List[DailyTaskSchedule] = []
        self.telemetry_records: List[Telemetry] = []

        # Statistics
        self.stats = {
            "unfastened_seatbelt": 0,
            "safety_alerts": 0,
            "normal_sessions": 0,
            "anomalous_sessions": 0,
            "weather_distribution": {w: 0 for w in WEATHER_CONDITIONS},
            "fault_distribution": {f.fault_type: 0 for f in FAULTS},
            "fault_count": 0,
            "operational_count": 0,
            "tasks_affected_by_faults": 0,
            "total_estimated_time": 0.0,
            "total_actual_time": 0.0,
            "total_downtime": 0.0,
            "operator_sessions": {op.op_id: 0 for op in OPERATORS},
            "operator_idle_total": {op.op_id: 0.0 for op in OPERATORS},
            "operator_load_total": {op.op_id: 0 for op in OPERATORS},
        }

    def _next_uuid(self) -> uuid.UUID:
        """Returns a deterministic UUID based on the seed and counter."""
        self._uuid_counter += 1
        return uuid.uuid5(uuid.NAMESPACE_OID, f"{self.seed}-{self._uuid_counter}")

    def generate(self) -> Tuple[List[TaskHistory], List[MachineFault], List[DailyTaskSchedule], List[Telemetry]]:
        """Run the full generation pipeline in FK-safe order."""
        start_date = date.today() - timedelta(days=self.days)

        for day_offset in range(self.days):
            current_date = start_date + timedelta(days=day_offset)
            self._generate_day(current_date)

        self._post_process_engine_hours()

        return self.task_histories, self.machine_faults, self.daily_schedules, self.telemetry_records

    def _generate_day(self, current_date: date):
        """Generate tasks, faults, schedules, and telemetry for one day."""
        # Randomly assign 2-4 operators per day
        active_operators = random.sample(OPERATORS, random.randint(2, len(OPERATORS)))
        
        for op in active_operators:
            # Operator might do 1-2 tasks a day
            num_tasks = random.randint(1, 2)
            for task_idx in range(num_tasks):
                # Pick machine and task type
                machine = random.choice(MACHINES)
                task_profile = random.choice(TASKS)
                weather = random.choices(WEATHER_CONDITIONS, weights=WEATHER_PROBABILITIES)[0]
                self.stats["weather_distribution"][weather] += 1
                
                # Determine if anomaly session
                is_anomaly = False
                if op.anomaly_type and random.random() < op.anomaly_prob:
                    is_anomaly = True
                    self.stats["anomalous_sessions"] += 1
                else:
                    self.stats["normal_sessions"] += 1

                self.stats["operator_sessions"][op.op_id] += 1

                # 1. Generate Task History
                task_id = f"TASK-{current_date.strftime('%Y%m%d')}-{op.op_id}-{task_idx}"
                
                # Base estimated time
                est_time = max(0.5, random.gauss(task_profile.estimated_mean, task_profile.estimated_std))
                self.stats["total_estimated_time"] += est_time

                # 2. Determine Faults & Downtime
                has_fault = random.random() < 0.1  # 10% chance of fault
                downtime_minutes = 0.0
                
                if has_fault:
                    fault_profile = random.choice(FAULTS)
                    downtime_minutes = max(5.0, random.gauss(fault_profile.downtime_mean, fault_profile.downtime_std))
                    self.stats["fault_count"] += 1
                    self.stats["tasks_affected_by_faults"] += 1
                    self.stats["fault_distribution"][fault_profile.fault_type] += 1
                    self.stats["total_downtime"] += downtime_minutes
                    
                    self.machine_faults.append(MachineFault(
                        id=self._next_uuid(),
                        task_id=task_id,
                        machine_status="Fault",
                        fault_type=fault_profile.fault_type,
                        downtime=downtime_minutes
                    ))
                else:
                    self.stats["operational_count"] += 1
                    self.machine_faults.append(MachineFault(
                        id=self._next_uuid(),
                        task_id=task_id,
                        machine_status="Operational",
                        fault_type=None,
                        downtime=0.0
                    ))

                # Calculate actual time: Explicit causal relationship
                # actual = estimated + (downtime in hours) + skill/weather noise
                skill_noise = {"Beginner": 0.5, "Intermediate": 0.0, "Expert": -0.5}[op.skill]
                weather_noise = {"Clear": 0.0, "Cloudy": 0.1, "Rainy": 0.8, "Windy": 0.5}[weather]
                random_noise = random.uniform(-0.5, 0.5)
                
                downtime_hours = downtime_minutes / 60.0
                actual_time = max(0.5, est_time + downtime_hours + skill_noise + weather_noise + random_noise)
                self.stats["total_actual_time"] += actual_time

                task_history = TaskHistory(
                    id=self._next_uuid(),
                    task_id=task_id,
                    task_type=task_profile.task_type,
                    weather=weather,
                    operator_skill=op.skill,
                    machine_age=machine.age,
                    estimated_time=est_time,
                    actual_time=actual_time
                )
                self.task_histories.append(task_history)

                # 3. Daily Task Schedule
                start_hour = 8 + (task_idx * 5) # e.g. 8 AM or 1 PM
                sched_time = time(hour=start_hour, minute=0)
                
                self.daily_schedules.append(DailyTaskSchedule(
                    schedule_id=self._next_uuid(),
                    task_id=task_id,
                    operator_id=op.op_id,
                    machine_id=machine.machine_id,
                    scheduled_date=current_date,
                    scheduled_time=sched_time,
                    task_status="Completed"
                ))

                # 4. Generate Telemetry for this session
                self._generate_telemetry(op, machine, current_date, sched_time, actual_time, is_anomaly)

    def _generate_telemetry(self, op: 'OperatorProfile', machine: 'MachineProfile', 
                            current_date: date, start_time: time, actual_time_hrs: float, is_anomaly: bool):
        # Generate a reading every 15 minutes of the actual task time
        num_readings = max(1, int(actual_time_hrs * 4))
        
        # Session baseline parameters based on anomaly profile
        idle_mean = op.idle_mean
        load_mean = op.load_cycles_mean
        
        if is_anomaly:
            if op.anomaly_type == "high_idling":
                idle_mean += 40.0 # Huge spike
            elif op.anomaly_type == "high_load_cycles":
                load_mean += 20.0 # Huge spike

        # Pre-calculate session totals for stats
        session_idle = 0.0
        session_load = 0

        # Create datetime start
        current_dt = datetime.combine(current_date, start_time).replace(tzinfo=timezone.utc)
        
        for i in range(num_readings):
            # Advance engine hours logically (15 mins = 0.25 hrs)
            self.engine_hours[machine.machine_id] += 0.25
            
            # Idling for this reading
            idle = max(0.0, random.gauss(idle_mean / num_readings, op.idle_std / max(1, (num_readings/2))))
            session_idle += idle
            
            # Load cycles for this reading
            load = max(0, int(random.gauss(load_mean / num_readings, op.load_cycles_std / max(1, (num_readings/2)))))
            session_load += load
            
            # Fuel correlates with load and inverse of idle
            fuel = (load * 2.5) + (idle * 0.1) + random.uniform(1.0, 3.0)

            # Safety
            unfastened = random.random() < op.unfastened_prob
            seatbelt_status = "Unfastened" if unfastened else "Fastened"
            if unfastened:
                self.stats["unfastened_seatbelt"] += 1
            
            # Safety alert triggered if unfastened and moving (load > 0)
            alert = unfastened and load > 0
            if alert:
                self.stats["safety_alerts"] += 1

            self.telemetry_records.append(Telemetry(
                id=self._next_uuid(),
                timestamp=current_dt,
                machine_id=machine.machine_id,
                operator_id=op.op_id,
                engine_hours=0.0, # Placeholder, set in post-processing
                fuel_used=fuel,
                load_cycles=load,
                idling_time=idle,
                seatbelt_status=seatbelt_status,
                safety_alert_triggered=alert
            ))
            
            current_dt += timedelta(minutes=15)

        self.stats["operator_idle_total"][op.op_id] += session_idle
        self.stats["operator_load_total"][op.op_id] += session_load

    def _post_process_engine_hours(self):
        # Sort telemetry by machine_id and timestamp to assign monotonically increasing engine hours
        self.telemetry_records.sort(key=lambda t: (t.machine_id, t.timestamp))
        for t in self.telemetry_records:
            self.engine_hours[t.machine_id] += 0.25
            t.engine_hours = self.engine_hours[t.machine_id]

    def print_summary(self):
        """Prints the specific requested generation statistics format."""
        
        # Calculate averages safely
        avg_est = self.stats["total_estimated_time"] / max(1, len(self.task_histories))
        avg_act = self.stats["total_actual_time"] / max(1, len(self.task_histories))
        avg_downtime = self.stats["total_downtime"] / max(1, self.stats["fault_count"])

        print("\n========== SYNTHETIC DATA GENERATION ==========")
        print(f"Seed: {self.seed}")
        print(f"Days: {self.days}")
        print("")
        print(f"Operators: {len(OPERATORS)}")
        print(f"Machines: {len(MACHINES)}")
        print(f"Tasks: {len(self.task_histories)}")
        print(f"Telemetry Records: {len(self.telemetry_records)}")
        print(f"Fault Events: {len(self.machine_faults)}")
        print(f"Daily Schedules: {len(self.daily_schedules)}")
        print("")
        print(f"Seatbelt Unfastened Events: {self.stats['unfastened_seatbelt']}")
        print(f"Safety Alert Records: {self.stats['safety_alerts']}")
        print("")
        print(f"Normal Sessions: {self.stats['normal_sessions']}")
        print(f"Anomalous Sessions: {self.stats['anomalous_sessions']}")
        print("")
        print("Weather Distribution:")
        for w in WEATHER_CONDITIONS:
            print(f"  {w}: {self.stats['weather_distribution'][w]}")
        print("")
        print("Fault Distribution:")
        for f in FAULTS:
            print(f"  {f.fault_type}: {self.stats['fault_distribution'][f.fault_type]}")
        print(f"  Operational (No Fault): {self.stats['operational_count']}")
        print("")
        print(f"Average Estimated Time: {avg_est:.2f}")
        print(f"Average Actual Time: {avg_act:.2f}")
        print(f"Average Fault Downtime: {avg_downtime:.2f}")
        print("")
        print("--- Operator Baselines & Anomalies (Averages per Session) ---")
        for op in OPERATORS:
            sessions = max(1, self.stats['operator_sessions'][op.op_id])
            avg_idle = self.stats['operator_idle_total'][op.op_id] / sessions
            avg_load = self.stats['operator_load_total'][op.op_id] / sessions
            print(f"  {op.op_id}: Sessions={sessions}, Avg Idle={avg_idle:.1f}m, Avg Loads={avg_load:.1f}")
        
        print("\nGeneration: SUCCESS")
        print("===============================================")
