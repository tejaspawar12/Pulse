"""
Seed script for 58 core exercises.
Only seeds if exercise_library table is empty.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models.exercise import ExerciseLibrary
import uuid

# 58 Core Exercises with stable UUIDs
EXERCISES = [
    # Upper Body - Chest (8 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Bench Press",
        "normalized_name": "bench press",
        "primary_muscle_group": "chest",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["bench", "bp", "flat bench", "barbell bench"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Incline Bench Press",
        "normalized_name": "incline bench press",
        "primary_muscle_group": "chest",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["incline bench", "incline bp", "incline barbell bench"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000001")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Dumbbell Bench Press",
        "normalized_name": "dumbbell bench press",
        "primary_muscle_group": "chest",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db bench", "dumbbell press", "db press"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000001")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "name": "Incline Dumbbell Press",
        "normalized_name": "incline dumbbell press",
        "primary_muscle_group": "chest",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["incline db press", "incline dumbbell bench"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000003")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
        "name": "Cable Flyes",
        "normalized_name": "cable flyes",
        "primary_muscle_group": "chest",
        "equipment": "cable",
        "movement_type": "strength",
        "aliases": ["cable fly", "cable crossover", "pec fly"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000006"),
        "name": "Dumbbell Flyes",
        "normalized_name": "dumbbell flyes",
        "primary_muscle_group": "chest",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db fly", "dumbbell fly", "pec fly db"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000005")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000007"),
        "name": "Push-ups",
        "normalized_name": "push-ups",
        "primary_muscle_group": "chest",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["pushup", "push up", "press up"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000008"),
        "name": "Dips",
        "normalized_name": "dips",
        "primary_muscle_group": "chest",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["chest dips", "dip"],
        "variation_of": None
    },
    
    # Upper Body - Back (10 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000009"),
        "name": "Barbell Row",
        "normalized_name": "barbell row",
        "primary_muscle_group": "back",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["bent over row", "barbell bent row", "row"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000010"),
        "name": "Dumbbell Row",
        "normalized_name": "dumbbell row",
        "primary_muscle_group": "back",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db row", "one arm row", "dumbbell bent row"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000009")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000011"),
        "name": "Pull-ups",
        "normalized_name": "pull-ups",
        "primary_muscle_group": "back",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["pullup", "pull up", "chin up overhand"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000012"),
        "name": "Chin-ups",
        "normalized_name": "chin-ups",
        "primary_muscle_group": "back",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["chinup", "chin up", "pull up underhand"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000011")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000013"),
        "name": "Lat Pulldown",
        "normalized_name": "lat pulldown",
        "primary_muscle_group": "back",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["lat pull", "pulldown", "lat pull down"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000014"),
        "name": "Cable Row",
        "normalized_name": "cable row",
        "primary_muscle_group": "back",
        "equipment": "cable",
        "movement_type": "strength",
        "aliases": ["seated cable row", "cable seated row", "row machine"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000015"),
        "name": "T-Bar Row",
        "normalized_name": "t-bar row",
        "primary_muscle_group": "back",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["t bar row", "tbar row", "t-bar"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000016"),
        "name": "Face Pulls",
        "normalized_name": "face pulls",
        "primary_muscle_group": "back",
        "equipment": "cable",
        "movement_type": "strength",
        "aliases": ["face pull", "rear delt cable"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000017"),
        "name": "Shrugs (Barbell)",
        "normalized_name": "shrugs (barbell)",
        "primary_muscle_group": "back",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["barbell shrug", "bb shrug", "shrug"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000018"),
        "name": "Shrugs (Dumbbell)",
        "normalized_name": "shrugs (dumbbell)",
        "primary_muscle_group": "back",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db shrug", "dumbbell shrug"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000017")
    },
    
    # Upper Body - Shoulders (6 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000019"),
        "name": "Overhead Press",
        "normalized_name": "overhead press",
        "primary_muscle_group": "shoulders",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["ohp", "shoulder press", "barbell press", "military press"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000020"),
        "name": "Dumbbell Shoulder Press",
        "normalized_name": "dumbbell shoulder press",
        "primary_muscle_group": "shoulders",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db shoulder press", "db press", "dumbbell ohp"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000019")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000021"),
        "name": "Lateral Raises",
        "normalized_name": "lateral raises",
        "primary_muscle_group": "shoulders",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["side raise", "lateral raise", "db lateral"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000022"),
        "name": "Front Raises",
        "normalized_name": "front raises",
        "primary_muscle_group": "shoulders",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["front raise", "db front raise"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000023"),
        "name": "Rear Delt Flyes",
        "normalized_name": "rear delt flyes",
        "primary_muscle_group": "shoulders",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["rear delt fly", "rear fly", "reverse fly"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000024"),
        "name": "Upright Row",
        "normalized_name": "upright row",
        "primary_muscle_group": "shoulders",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["upright barbell row", "bb upright row"],
        "variation_of": None
    },
    
    # Upper Body - Arms (7 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000025"),
        "name": "Bicep Curls (Barbell)",
        "normalized_name": "bicep curls (barbell)",
        "primary_muscle_group": "arms",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["bb curl", "barbell curl", "bicep curl"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000026"),
        "name": "Bicep Curls (Dumbbell)",
        "normalized_name": "bicep curls (dumbbell)",
        "primary_muscle_group": "arms",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["db curl", "dumbbell curl", "db bicep curl"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000025")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000027"),
        "name": "Hammer Curls",
        "normalized_name": "hammer curls",
        "primary_muscle_group": "arms",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["hammer curl", "neutral grip curl"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000028"),
        "name": "Tricep Dips",
        "normalized_name": "tricep dips",
        "primary_muscle_group": "arms",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["tricep dip", "triceps dip", "bench dip"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000029"),
        "name": "Tricep Pushdown",
        "normalized_name": "tricep pushdown",
        "primary_muscle_group": "arms",
        "equipment": "cable",
        "movement_type": "strength",
        "aliases": ["tricep push down", "cable pushdown", "triceps extension"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000030"),
        "name": "Overhead Tricep Extension",
        "normalized_name": "overhead tricep extension",
        "primary_muscle_group": "arms",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["oh tricep extension", "overhead extension", "db tricep extension"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000031"),
        "name": "Close-Grip Bench Press",
        "normalized_name": "close-grip bench press",
        "primary_muscle_group": "arms",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["close grip bench", "cg bench", "close grip bp"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000001")
    },
    
    # Lower Body - Quads (8 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000032"),
        "name": "Squat",
        "normalized_name": "squat",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["back squat", "barbell squat", "bs"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000033"),
        "name": "Front Squat",
        "normalized_name": "front squat",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["front squat", "fs"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000032")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000034"),
        "name": "Leg Press",
        "normalized_name": "leg press",
        "primary_muscle_group": "legs",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["leg press machine", "hack squat machine"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000035"),
        "name": "Leg Extensions",
        "normalized_name": "leg extensions",
        "primary_muscle_group": "legs",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["leg extension", "quad extension", "knee extension"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000036"),
        "name": "Bulgarian Split Squats",
        "normalized_name": "bulgarian split squats",
        "primary_muscle_group": "legs",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["bulgarian split squat", "bss", "rear foot elevated split squat"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000037"),
        "name": "Lunges",
        "normalized_name": "lunges",
        "primary_muscle_group": "legs",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["lunge", "walking lunge", "db lunge"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000038"),
        "name": "Step-ups",
        "normalized_name": "step-ups",
        "primary_muscle_group": "legs",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["step up", "box step up", "stepup"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000039"),
        "name": "Goblet Squat",
        "normalized_name": "goblet squat",
        "primary_muscle_group": "legs",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["goblet", "db goblet squat"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000032")
    },
    
    # Lower Body - Hamstrings & Glutes (6 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000040"),
        "name": "Deadlift",
        "normalized_name": "deadlift",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["conventional deadlift", "dl", "barbell deadlift"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000041"),
        "name": "Romanian Deadlift",
        "normalized_name": "romanian deadlift",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["rdl", "romanian dl", "stiff leg deadlift variation"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000040")
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000042"),
        "name": "Leg Curls",
        "normalized_name": "leg curls",
        "primary_muscle_group": "legs",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["leg curl", "hamstring curl", "lying leg curl"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000043"),
        "name": "Hip Thrusts",
        "normalized_name": "hip thrusts",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["hip thrust", "glute bridge", "barbell hip thrust"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000044"),
        "name": "Good Mornings",
        "normalized_name": "good mornings",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["good morning", "barbell good morning"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000045"),
        "name": "Stiff Leg Deadlift",
        "normalized_name": "stiff leg deadlift",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["sldl", "stiff leg dl", "straight leg deadlift"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000040")
    },
    
    # Lower Body - Calves (2 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000046"),
        "name": "Calf Raises (Standing)",
        "normalized_name": "calf raises (standing)",
        "primary_muscle_group": "legs",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["standing calf raise", "calf raise", "bb calf raise"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000047"),
        "name": "Calf Raises (Seated)",
        "normalized_name": "calf raises (seated)",
        "primary_muscle_group": "legs",
        "equipment": "machine",
        "movement_type": "strength",
        "aliases": ["seated calf raise", "seated calf"],
        "variation_of": uuid.UUID("00000000-0000-0000-0000-000000000046")
    },
    
    # Core (6 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000048"),
        "name": "Plank",
        "normalized_name": "plank",
        "primary_muscle_group": "core",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["front plank", "plank hold"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000049"),
        "name": "Crunches",
        "normalized_name": "crunches",
        "primary_muscle_group": "core",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["crunch", "ab crunch", "sit up"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000050"),
        "name": "Russian Twists",
        "normalized_name": "russian twists",
        "primary_muscle_group": "core",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["russian twist", "seated twist"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000051"),
        "name": "Leg Raises",
        "normalized_name": "leg raises",
        "primary_muscle_group": "core",
        "equipment": "bodyweight",
        "movement_type": "strength",
        "aliases": ["leg raise", "hanging leg raise", "lying leg raise"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000052"),
        "name": "Cable Crunches",
        "normalized_name": "cable crunches",
        "primary_muscle_group": "core",
        "equipment": "cable",
        "movement_type": "strength",
        "aliases": ["cable crunch", "kneeling cable crunch"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000053"),
        "name": "Ab Wheel Rollout",
        "normalized_name": "ab wheel rollout",
        "primary_muscle_group": "core",
        "equipment": "other",
        "movement_type": "strength",
        "aliases": ["ab wheel", "ab roller", "wheel rollout"],
        "variation_of": None
    },
    
    # Full Body / Cardio (5 exercises)
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000054"),
        "name": "Burpees",
        "normalized_name": "burpees",
        "primary_muscle_group": "full_body",
        "equipment": "bodyweight",
        "movement_type": "cardio",
        "aliases": ["burpee", "burpy"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000055"),
        "name": "Mountain Climbers",
        "normalized_name": "mountain climbers",
        "primary_muscle_group": "full_body",
        "equipment": "bodyweight",
        "movement_type": "cardio",
        "aliases": ["mountain climber", "running plank"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000056"),
        "name": "Kettlebell Swings",
        "normalized_name": "kettlebell swings",
        "primary_muscle_group": "full_body",
        "equipment": "kettlebell",
        "movement_type": "cardio",
        "aliases": ["kb swing", "kettlebell swing", "swing"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000057"),
        "name": "Farmer's Walk",
        "normalized_name": "farmer's walk",
        "primary_muscle_group": "full_body",
        "equipment": "dumbbell",
        "movement_type": "strength",
        "aliases": ["farmer walk", "farmers walk", "carry"],
        "variation_of": None
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000058"),
        "name": "Thruster",
        "normalized_name": "thruster",
        "primary_muscle_group": "full_body",
        "equipment": "barbell",
        "movement_type": "strength",
        "aliases": ["thrusters", "squat press"],
        "variation_of": None
    },
]

def seed_exercises():
    db: Session = SessionLocal()
    try:
        # Check if table is empty
        count = db.query(ExerciseLibrary).count()
        if count > 0:
            print(f"Exercise library already has {count} exercises. Skipping seed.")
            return
        
        # Seed exercises
        for exercise_data in EXERCISES:
            exercise = ExerciseLibrary(**exercise_data)
            db.add(exercise)
        
        db.commit()
        print(f"Successfully seeded {len(EXERCISES)} exercises.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding exercises: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()
