"""
Seed script for Phase 5 Training Hub.
Creates training tables and injects the Seatbelt Safety Fundamentals module.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.models.training import TrainingModule, TrainingQuestion

def run_seed():
    print("Creating Phase 5 Training Tables...")
    Base.metadata.create_all(engine)
    
    print("Seeding Seatbelt Safety Module...")
    with Session(engine) as db:
        # Check if already exists
        existing = db.query(TrainingModule).filter(TrainingModule.title == "Seatbelt Safety Fundamentals").first()
        if existing:
            print("Module already exists, skipping seed.")
            return

        module = TrainingModule(
            title="Seatbelt Safety Fundamentals",
            category="Seatbelt Safety",
            description="A critical safety module detailing the risks of unfastened operation and the standard protocols for operator securement.",
            duration_minutes=5,
            difficulty="Beginner"
        )
        
        db.add(module)
        db.flush() # To get the module_id
        
        # Add questions
        q1 = TrainingQuestion(
            module_id=module.module_id,
            question_text="What is the primary risk of operating machinery with an unfastened seatbelt?",
            options=["Operator ejection during sudden stops", "Reduced engine efficiency", "Increased cabin noise", "Hydraulic pressure loss"],
            correct_answer="Operator ejection during sudden stops",
            explanation="The primary safety risk of an unfastened seatbelt is operator ejection or severe injury during sudden deceleration, rollover, or collision."
        )
        
        q2 = TrainingQuestion(
            module_id=module.module_id,
            question_text="When must the seatbelt be fastened?",
            options=["Only when operating on steep inclines", "Before the engine is started and for the entire duration of operation", "Only when carrying heavy loads", "After leaving the loading zone"],
            correct_answer="Before the engine is started and for the entire duration of operation",
            explanation="Safety protocols require the seatbelt to be fastened before the engine starts and to remain fastened at all times while the machine is operating."
        )
        
        q3 = TrainingQuestion(
            module_id=module.module_id,
            question_text="How often should the seatbelt mechanism be inspected for wear?",
            options=["Every 5 years", "Only when a fault code appears", "During the daily pre-operation inspection", "Monthly during scheduled maintenance"],
            correct_answer="During the daily pre-operation inspection",
            explanation="Seatbelts are critical safety devices and must be inspected for fraying, latch functionality, and mounting security during every daily pre-op check."
        )
        
        db.add_all([q1, q2, q3])
        db.commit()
        print(f"Successfully seeded Module '{module.title}' with 3 questions.")

if __name__ == "__main__":
    run_seed()
