from sqlalchemy import Column, String, ARRAY, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import Base

class ExerciseLibrary(Base):
    __tablename__ = "exercise_library"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, index=True)  # lowercase + trimmed
    primary_muscle_group = Column(String, nullable=False)  # chest, back, legs, etc.
    equipment = Column(String, nullable=False)  # barbell, dumbbell, machine, etc.
    movement_type = Column(String, nullable=False)  # strength, cardio
    aliases = Column(ARRAY(String), server_default=text("'{}'"), nullable=False)  # lowercase strings, DB default
    variation_of = Column(UUID(as_uuid=True), ForeignKey("exercise_library.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
