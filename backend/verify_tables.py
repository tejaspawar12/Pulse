from app.config.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)

print("📊 Tables in database:")
tables = inspector.get_table_names()
for table in sorted(tables):
    print(f"  ✅ {table}")

print("\n📑 Indexes:")
for table_name in tables:
    indexes = inspector.get_indexes(table_name)
    if indexes:
        print(f"\n  {table_name}:")
        for idx in indexes:
            print(f"    - {idx['name']}")

print("\n🔍 Checking pg_trgm extension:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'pg_trgm'"))
    if result.fetchone():
        print("  ✅ pg_trgm extension enabled")
    else:
        print("  ❌ pg_trgm extension NOT found")

print("\n🔒 Checking partial unique index:")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname = 'unique_active_draft_per_user'
    """))
    if result.fetchone():
        print("  ✅ unique_active_draft_per_user index exists")
    else:
        print("  ❌ unique_active_draft_per_user index NOT found")
