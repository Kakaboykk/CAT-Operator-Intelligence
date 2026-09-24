"""
CLI Script to generate synthetic data for Phase 2.
"""
import argparse
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.data_generation.generator import SyntheticDataGenerator
from app.data_generation.db_operations import reset_phase2_data, bulk_insert_generated_data


def main():
    parser = argparse.ArgumentParser(description="CAT Operator Synthetic Data Generator")
    parser.add_argument("--seed", type=int, required=True, help="Random seed for deterministic generation")
    parser.add_argument("--reset", action="store_true", help="Clear existing Phase 2 generated data before inserting")
    parser.add_argument("--days", type=int, default=30, help="Number of days of data to generate (default 30)")
    args = parser.parse_args()

    print(f"Initializing Phase 2 Generator with seed {args.seed}...")
    generator = SyntheticDataGenerator(seed=args.seed, days=args.days)
    
    tasks, faults, schedules, telemetries = generator.generate()

    with SessionLocal() as db:
        if args.reset:
            reset_phase2_data(db)
        
        # Insert in FK-safe order
        print("Inserting records transactionally...")
        # Since db_operations bulk insert handles all of them, we pass them ordered correctly.
        all_records = []
        all_records.extend(tasks)
        all_records.extend(faults)
        all_records.extend(schedules)
        all_records.extend(telemetries)
        
        bulk_insert_generated_data(db, all_records)

    generator.print_summary()


if __name__ == "__main__":
    main()
