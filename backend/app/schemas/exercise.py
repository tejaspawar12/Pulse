"""
Exercise schemas for API responses.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class ExerciseOut(BaseModel):
    """Response schema for an exercise."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    primary_muscle_group: str
    equipment: str
    movement_type: str
    variation_of: Optional[UUID] = None


class ExerciseListOut(BaseModel):
    """Response schema for exercise list."""
    model_config = ConfigDict(from_attributes=True)
    
    exercises: List[ExerciseOut]
