from sqlalchemy import Column, Date, Boolean, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import Base

class DailyTrainingState(Base):
    __tablename__ = "daily_training_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)  # Computed using AT TIME ZONE
    worked_out = Column(Boolean, default=False, nullable=False)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )
