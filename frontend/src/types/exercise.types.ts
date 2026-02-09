/**
 * Exercise types matching backend schemas.
 * Shared API contract - must match backend exactly.
 */

export interface Exercise {
  id: string;
  name: string;
  primary_muscle_group: string;
  equipment: string;
  movement_type: string;
  variation_of?: string; // UUID string or null
}

export interface ExerciseList {
  exercises: Exercise[];
}
