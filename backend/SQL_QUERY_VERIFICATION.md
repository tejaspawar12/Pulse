# SQL Query Count Verification Guide

**Purpose**: Verify that endpoints use efficient queries (no N+1 queries)

**Date**: January 31, 2026  
**Status**: Manual verification task

---

## Steps to Verify Query Counts

### 1. Temporarily Enable SQL Logging

**File**: `backend/app/config/database.py`

**Change**:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# TEMPORARY: Enable SQL logging for query count verification
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True,
    echo=True  # ⚠️ TEMPORARY - Remove after verification
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 2. Start Backend Server

```powershell
cd A:\SuNaAI-Lab\fitness\backend
..\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 3. Test Each Endpoint

#### History Endpoint
**Request**: `GET /api/v1/workouts?limit=20`

**Expected Query Count**: 1-2 queries
- 1 main query with SQL aggregates
- Optional: 1 count query (if needed)

**Verify**:
- No per-row queries
- SQL aggregates used (exercise_count, set_count)
- Date computed in SQL

#### Workout Detail Endpoint
**Request**: `GET /api/v1/workouts/{workout_id}`

**Expected Query Count**: 1 query
- 1 query with eager loading (selectinload)

**Verify**:
- Exercises loaded in same query
- Sets loaded in same query
- No lazy loading

#### Finish Workout Endpoint
**Request**: `POST /api/v1/workouts/{workout_id}/finish`

**Expected Query Count**: 2-3 queries
- 1 query to get workout (with eager loading)
- 1 query for daily_training_state upsert
- Optional: 1 query for duration calculation

**Verify**:
- No N+1 queries
- Eager loading used
- Efficient upsert

### 4. Count Queries in Logs

**Look for**:
- `SELECT` statements in logs
- Count total SELECT queries per endpoint
- Verify counts match expected values

### 5. Remove echo=True

**File**: `backend/app/config/database.py`

**Revert to**:
```python
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
    # echo=True removed
)
```

---

## Expected Results

| Endpoint | Expected Queries | Status |
|----------|-----------------|--------|
| History | 1-2 | ⏳ To verify |
| Workout Detail | 1 | ⏳ To verify |
| Finish Workout | 2-3 | ⏳ To verify |
| Previous Performance | 1-2 | ⏳ To verify |

---

## Notes

- **N+1 Query Problem**: When you fetch a list and then fetch related data for each item separately
- **Solution**: Use SQL aggregates or eager loading
- **Verification**: Count SELECT statements in logs

---

**Document Version**: 1.0  
**Last Updated**: January 31, 2026  
**Status**: Manual verification task
