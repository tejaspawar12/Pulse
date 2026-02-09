"""Check workouts.start_time column type."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='workouts' AND column_name='start_time'
    """))
    row = result.first()
    if row:
        print(f"Column: {row[0]}, Type: {row[1]}")
        if 'time zone' in row[1].lower() or 'timestamptz' in row[1].lower():
            print("✅ Column is TIMESTAMPTZ - correct!")
        else:
            print("❌ Column is NOT TIMESTAMPTZ - needs migration!")
    else:
        print("❌ Column not found!")
