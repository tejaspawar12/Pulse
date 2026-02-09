from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, func, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base
from app.utils.enums import LifecycleStatus, CompletionStatus, RPE, SetType

# Import ExerciseLibrary to ensure SQLAlchemy can resolve the relationship
# This must be imported before WorkoutExercise uses it in a relationship
from app.models.exercise import ExerciseLibrary

class Workout(Base):
    __tablename__ = "workouts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lifecycle_status = Column(String, nullable=False, default=LifecycleStatus.DRAFT.value)
    completion_status = Column(String, nullable=True)  # Only set when finalized
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    name = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout",
        order_by="WorkoutExercise.order_index",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_workouts_user_start', 'user_id', text('start_time DESC')),
        Index('idx_workouts_user_completion', 'user_id', 'completion_status', text('start_time DESC')),
    )

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercise_library.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("ExerciseLibrary")
    sets = relationship(
        "WorkoutSet",
        back_populates="workout_exercise",
        order_by="WorkoutSet.set_number",
        cascade="all, delete-orphan"
    )
    
    @property
    def exercise_name(self) -> str:
        """Get exercise name from relationship.
        
        This property allows Pydantic to read exercise_name naturally
        via model_validate() without manual patching.
        
        Pydantic v2 models are immutable by default, so manual patching
        like `exercise_out.exercise_name = we.exercise.name` is fragile.
        This property approach is cleaner and more maintainable.
        """
        return self.exercise.name if self.exercise else ""
    
    __table_args__ = (
        Index('idx_workout_exercises_workout_order', 'workout_id', 'order_index'),
    )

class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_exercise_id = Column(UUID(as_uuid=True), ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False)
    set_number = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=True)
    weight = Column(Numeric(6, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # For time-based exercises
    rpe = Column(String, nullable=True)
    set_type = Column(String, nullable=False, default=SetType.WORKING.value)
    rest_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    workout_exercise = relationship("WorkoutExercise", back_populates="sets")
    
    __table_args__ = (
        Index('idx_workout_sets_exercise_set', 'workout_exercise_id', 'set_number'),
    )
