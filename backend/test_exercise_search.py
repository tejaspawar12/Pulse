from app.config.database import SessionLocal
from app.models.exercise import ExerciseLibrary
from sqlalchemy import text, or_, func

db = SessionLocal()

try:
    # Test normalized name search
    query = "bench"
    results = db.query(ExerciseLibrary).filter(
        ExerciseLibrary.normalized_name.ilike(f"%{query.lower()}%")
    ).all()
    
    print(f"🔍 Search for '{query}': {len(results)} results")
    for ex in results[:5]:
        print(f"  - {ex.name}")
    
    # Test alias search
    query = "bp"
    results = db.query(ExerciseLibrary).filter(
        func.lower(query) == func.any_(ExerciseLibrary.aliases)
    ).all()
    
    print(f"\n🔍 Alias search for '{query}': {len(results)} results")
    for ex in results:
        print(f"  - {ex.name} (aliases: {ex.aliases})")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
