/**
 * Workout types matching backend schemas.
 * Shared API contract - must match backend exactly.
 */

export enum LifecycleStatus {
  DRAFT = 'draft',
  FINALIZED = 'finalized',
  ABANDONED = 'abandoned',
}

export enum CompletionStatus {
  COMPLETED = 'completed',
  PARTIAL = 'partial',
}

export enum RPE {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard',
}

export enum SetType {
  WORKING = 'working',
  WARMUP = 'warmup',
  FAILURE = 'failure',
  DROP = 'drop',
  AMRAP = 'amrap',
}

export interface WorkoutSet {
  id: string;
  set_number: number;
  reps?: number;
  weight?: number;
  duration_seconds?: number;
  rpe?: RPE;
  set_type: SetType;
  rest_time_seconds?: number;
  created_at: string; // ISO datetime
}

export interface WorkoutExercise {
  id: string;
  exercise_id: string;
  exercise_name: string;
  order_index: number;
  notes?: string;
  sets: WorkoutSet[];
  created_at: string; // ISO datetime
}

export interface WorkoutOut {
  id: string;
  user_id: string;
  lifecycle_status: LifecycleStatus;
  completion_status?: CompletionStatus;
  start_time: string; // ISO datetime (timezone-aware)
  end_time?: string; // ISO datetime
  duration_minutes?: number;
  name?: string;
  notes?: string;
  exercises: WorkoutExercise[];
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface ActiveWorkoutSummary {
  id: string;
  date: string; // YYYY-MM-DD
  name?: string;
  exercise_count: number;
  set_count: number;
  start_time: string; // ISO datetime (timezone-aware)
}

export interface WorkoutSummary {
  id: string;
  date: string; // YYYY-MM-DD
  name?: string;
  duration_minutes?: number;
  exercise_count: number;
  set_count: number;
  completion_status: CompletionStatus;
}

export interface DailyStatus {
  date: string; // YYYY-MM-DD
  worked_out: boolean;
}

export interface UserStatusOut {
  active_workout: ActiveWorkoutSummary | null;
  today_worked_out: boolean;
  last_30_days: DailyStatus[]; // Ordered: oldest → newest
}

export interface PreviousSetPerformance {
  set_number: number;
  reps?: number;
  weight?: number;
  duration_seconds?: number;
  set_type: SetType;
}

export interface LastPerformance {
  last_date: string; // ISO date string (YYYY-MM-DD)
  workout_id: string;
  sets: PreviousSetPerformance[];
}
