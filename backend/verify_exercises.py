from app.config.database import SessionLocal
from app.models.exercise import ExerciseLibrary
from sqlalchemy import func

db = SessionLocal()

try:
    # Count exercises
    count = db.query(ExerciseLibrary).count()
    print(f"📊 Total exercises: {count}")
    
    # Count by muscle group
    print("\n📑 Exercises by muscle group:")
    muscle_groups = db.query(
        ExerciseLibrary.primary_muscle_group,
        func.count(ExerciseLibrary.id).label('count')
    ).group_by(ExerciseLibrary.primary_muscle_group).all()
    
    for mg, cnt in muscle_groups:
        print(f"  {mg}: {cnt}")
    
    # Count by equipment
    print("\n🔧 Exercises by equipment:")
    equipment = db.query(
        ExerciseLibrary.equipment,
        func.count(ExerciseLibrary.id).label('count')
    ).group_by(ExerciseLibrary.equipment).all()
    
    for eq, cnt in equipment:
        print(f"  {eq}: {cnt}")
    
    # Check variations
    print("\n🔗 Exercise variations:")
    variations = db.query(ExerciseLibrary).filter(
        ExerciseLibrary.variation_of.isnot(None)
    ).count()
    print(f"  Exercises with variations: {variations}")
    
    # Sample exercises
    print("\n📋 Sample exercises:")
    samples = db.query(ExerciseLibrary).limit(5).all()
    for ex in samples:
        print(f"  - {ex.name} ({ex.primary_muscle_group}, {ex.equipment})")
        if ex.aliases:
            print(f"    Aliases: {', '.join(ex.aliases)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
