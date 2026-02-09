"""
Quick script to abandon an old workout.
Run this to clear the old workout so you can start a new one.
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
# Import all models to ensure SQLAlchemy can resolve relationships
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.utils.enums import LifecycleStatus
from uuid import UUID

def abandon_workout(workout_id: str, user_id: str = None):
    """
    Abandon a workout by ID.
    
    Args:
        workout_id: Workout UUID (string)
        user_id: Optional user ID to verify ownership
    """
    db: Session = SessionLocal()
    
    try:
        workout = db.query(Workout).filter(Workout.id == UUID(workout_id)).first()
        
        if not workout:
            print(f"❌ Workout {workout_id} not found")
            return
        
        if user_id and str(workout.user_id) != user_id:
            print(f"❌ Workout belongs to different user")
            return
        
        if workout.lifecycle_status == LifecycleStatus.ABANDONED.value:
            print(f"✅ Workout {workout_id} is already abandoned")
            return
        
        # Abandon the workout
        workout.lifecycle_status = LifecycleStatus.ABANDONED.value
        workout.completion_status = None
        db.commit()
        
        print(f"✅ Workout {workout_id} abandoned successfully")
        print(f"   Status: {workout.lifecycle_status}")
        print(f"   Start time: {workout.start_time}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

def abandon_all_drafts_for_user(user_id: str):
    """
    Abandon all draft workouts for a user.
    
    Args:
        user_id: User UUID (string)
    """
    db: Session = SessionLocal()
    
    try:
        workouts = db.query(Workout).filter(
            Workout.user_id == UUID(user_id),
            Workout.lifecycle_status == LifecycleStatus.DRAFT.value
        ).all()
        
        if not workouts:
            print(f"✅ No draft workouts found for user {user_id}")
            return
        
        for workout in workouts:
            workout.lifecycle_status = LifecycleStatus.ABANDONED.value
            workout.completion_status = None
            print(f"   Abandoning workout {workout.id} (started: {workout.start_time})")
        
        db.commit()
        print(f"✅ Abandoned {len(workouts)} workout(s) for user {user_id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python abandon_old_workout.py <workout_id>")
        print("  python abandon_old_workout.py --user <user_id>  # Abandon all drafts for user")
        print("\nExample:")
        print("  python abandon_old_workout.py 431c759a-ced7-4fae-b3dd-8e897e0e58fb")
        print("  python abandon_old_workout.py --user 6b02afa2-2fe6-4140-9745-851c4bc0613f")
        sys.exit(1)
    
    if sys.argv[1] == "--user":
        if len(sys.argv) < 3:
            print("❌ Please provide user ID")
            sys.exit(1)
        abandon_all_drafts_for_user(sys.argv[2])
    else:
        workout_id = sys.argv[1]
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        abandon_workout(workout_id, user_id)
