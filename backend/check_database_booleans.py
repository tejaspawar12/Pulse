"""
Check if database has string booleans stored instead of proper booleans.
This script verifies the actual data type in the database.
"""
from app.config.database import engine
from sqlalchemy import text, inspect

print("🔍 Checking database for string booleans...\n")

with engine.connect() as conn:
    # 1. Check column type in daily_training_state
    print("1️⃣ Checking daily_training_state.worked_out column type:")
    result = conn.execute(text("""
        SELECT 
            column_name,
            data_type,
            udt_name
        FROM information_schema.columns
        WHERE table_name = 'daily_training_state' 
          AND column_name = 'worked_out'
    """))
    row = result.fetchone()
    if row:
        print(f"   Column: {row[0]}")
        print(f"   Data Type: {row[1]}")
        print(f"   UDT Name: {row[2]}")
        if row[1] != 'boolean':
            print(f"   ❌ WARNING: Column is {row[1]}, not boolean!")
        else:
            print(f"   ✅ Column type is correct (boolean)")
    else:
        print("   ❌ Column not found!")
    
    # 2. Check actual data in daily_training_state
    print("\n2️⃣ Checking actual data in daily_training_state:")
    result = conn.execute(text("""
        SELECT 
            id,
            user_id,
            date,
            worked_out,
            pg_typeof(worked_out) as actual_type
        FROM daily_training_state
        LIMIT 5
    """))
    rows = result.fetchall()
    if rows:
        print(f"   Found {len(rows)} rows:")
        for row in rows:
            print(f"   - worked_out: {row[3]} (type: {row[4]}, Python type: {type(row[3])})")
            if isinstance(row[3], str):
                print(f"     ❌ WARNING: This is a STRING, not boolean!")
    else:
        print("   ✅ No data in daily_training_state (this is OK - service computes from workouts)")
    
    # 3. Check if workouts table has any boolean columns that might be strings
    print("\n3️⃣ Checking workouts table structure:")
    result = conn.execute(text("""
        SELECT 
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_name = 'workouts'
        ORDER BY ordinal_position
    """))
    rows = result.fetchall()
    print("   Columns in workouts table:")
    for row in rows:
        print(f"   - {row[0]}: {row[1]}")
    
    # 4. Check if there's any data that might be causing issues
    print("\n4️⃣ Checking for any string 'true'/'false' in database:")
    result = conn.execute(text("""
        SELECT 
            'daily_training_state' as table_name,
            COUNT(*) as count
        FROM daily_training_state
        WHERE worked_out::text IN ('true', 'false', '"true"', '"false"')
    """))
    row = result.fetchone()
    if row and row[1] > 0:
        print(f"   ❌ WARNING: Found {row[1]} rows with string booleans in {row[0]}")
    else:
        print("   ✅ No string booleans found")
    
    # 5. Check PostgreSQL version and boolean handling
    print("\n5️⃣ Checking PostgreSQL version:")
    result = conn.execute(text("SELECT version()"))
    version = result.fetchone()[0]
    print(f"   {version}")

print("\n✅ Database check complete!")
