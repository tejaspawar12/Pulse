/**
 * Workout API methods.
 * Matches backend endpoints exactly.
 */
import { apiClient } from './client';
import { WorkoutOut, WorkoutSet, SetType, RPE, CompletionStatus, WorkoutSummary } from '../../types/workout.types';

export const workoutApi = {
  /**
   * Start a new workout or return existing draft.
   * POST /api/v1/workouts/start
   */
  async start(): Promise<WorkoutOut> {
    const res = await apiClient.post<WorkoutOut>('/workouts/start');
    return res.data;
  },

  /**
   * Get active draft workout.
   * GET /api/v1/workouts/active
   * Returns null if no active workout (backend returns 200 with null body).
   */
  async getActive(): Promise<WorkoutOut | null> {
    try {
      const res = await apiClient.get<WorkoutOut | null>('/workouts/active');
      
      // Backend returns 200 with null body if no workout (not 204)
      // Safer: check if data exists
      if (!res.data) {
        return null;
      }
      
      return res.data;
    } catch (error) {
      console.error('Error getting active workout:', error);
      throw error;
    }
  },

  /**
   * Add exercise to workout.
   * POST /api/v1/workouts/{id}/exercises
   * 
   * @param workoutId Workout UUID
   * @param request Exercise to add
   * @returns Updated workout with new exercise
   */
  async addExercise(
    workoutId: string,
    request: {
      exercise_id: string;
      order_index?: number;
      notes?: string;
    }
  ): Promise<WorkoutOut> {
    try {
      const res = await apiClient.post<WorkoutOut>(
        `/workouts/${workoutId}/exercises`,
        request
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error adding exercise:', error);
      throw error;
    }
  },

  /**
   * Add set to workout exercise.
   * POST /api/v1/workout-exercises/{id}/sets
   * 
   * @param workoutExerciseId Workout exercise UUID
   * @param request Set data
   * @returns Created set
   */
  async addSet(
    workoutExerciseId: string,
    request: {
      set_number?: number;
      reps?: number;
      weight?: number;
      duration_seconds?: number;
      set_type: SetType;
      rpe?: RPE;
      rest_time_seconds?: number;
    }
  ): Promise<WorkoutSet> {
    try {
      const res = await apiClient.post<WorkoutSet>(
        `/workout-exercises/${workoutExerciseId}/sets`,
        request
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error adding set:', error);
      throw error;
    }
  },

  /**
   * Update set (partial update).
   * PATCH /api/v1/sets/{id}
   * 
   * @param setId Set UUID
   * @param request Partial set data
   * @returns Updated set
   */
  async updateSet(
    setId: string,
    request: {
      reps?: number;
      weight?: number;
      duration_seconds?: number;
      set_type?: SetType;
      rpe?: RPE;
      rest_time_seconds?: number;
    }
  ): Promise<WorkoutSet> {
    try {
      const res = await apiClient.patch<WorkoutSet>(
        `/sets/${setId}`,
        request
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error updating set:', error);
      throw error;
    }
  },

  /**
   * Delete set.
   * DELETE /api/v1/sets/{id}
   * 
   * @param setId Set UUID
   */
  async deleteSet(setId: string): Promise<void> {
    try {
      await apiClient.delete(`/sets/${setId}`);
    } catch (error) {
      console.error('[workoutApi] Error deleting set:', error);
      throw error;
    }
  },

  /**
   * Reorder exercises in workout.
   * PATCH /api/v1/workouts/{id}/exercises/reorder
   * 
   * @param workoutId Workout UUID
   * @param request Reorder data
   * @returns Updated workout with reordered exercises
   */
  async reorderExercises(
    workoutId: string,
    request: {
      items: Array<{
        workout_exercise_id: string;
        order_index: number;
      }>;
    }
  ): Promise<WorkoutOut> {
    try {
      const res = await apiClient.patch<WorkoutOut>(
        `/workouts/${workoutId}/exercises/reorder`,
        request
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error reordering exercises:', error);
      throw error;
    }
  },

  /**
   * Discard (cancel) the current draft workout. Workout is abandoned and will not appear in history.
   * POST /api/v1/workouts/{id}/discard
   *
   * @param workoutId Workout UUID
   */
  async discardWorkout(workoutId: string): Promise<void> {
    try {
      await apiClient.post(`/workouts/${workoutId}/discard`);
    } catch (error) {
      console.error('[workoutApi] Error discarding workout:', error);
      throw error;
    }
  },

  /**
   * Finish workout (finalize).
   * POST /api/v1/workouts/{id}/finish
   * 
   * @param workoutId Workout UUID
   * @param completionStatus Completion status (completed or partial)
   * @param notes Optional workout notes
   * @returns Finalized workout
   */
  async finishWorkout(
    workoutId: string,
    completionStatus: CompletionStatus,
    notes?: string
  ): Promise<WorkoutOut> {
    try {
      const res = await apiClient.post<WorkoutOut>(
        `/workouts/${workoutId}/finish`,
        {
          completion_status: completionStatus,
          notes: notes || undefined
        }
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error finishing workout:', error);
      throw error;
    }
  },

  /**
   * Update workout name/notes (draft only).
   * PATCH /api/v1/workouts/{id}
   * 
   * @param workoutId Workout UUID
   * @param request Partial update (name and/or notes)
   * @returns Updated workout
   */
  async updateWorkout(
    workoutId: string,
    request: {
      name?: string;
      notes?: string;
    }
  ): Promise<WorkoutOut> {
    try {
      const res = await apiClient.patch<WorkoutOut>(
        `/workouts/${workoutId}`,
        request
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error updating workout:', error);
      throw error;
    }
  },

  /**
   * Get workout session by ID (for restoring after app kill).
   * GET /api/v1/workouts/{id}/session
   * 
   * @param workoutId Workout UUID
   * @returns Full workout with exercises and sets
   */
  async getWorkoutSession(workoutId: string): Promise<WorkoutOut> {
    try {
      const res = await apiClient.get<WorkoutOut>(
        `/workouts/${workoutId}/session`
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error getting workout session:', error);
      throw error;
    }
  },

  /**
   * Get workout history with pagination.
   * GET /api/v1/workouts?cursor=...&limit=...
   * 
   * ⚠️ LOCKED RULE: Always use URLSearchParams for cursor (contains : and |)
   * Never use string concatenation - URLSearchParams handles encoding correctly
   * 
   * @param cursor Optional cursor for pagination (ISO UTC timestamp with Z)
   * @param limit Maximum number of items (default 20)
   * @returns History list with next cursor
   */
  async getHistory(
    cursor?: string,
    limit: number = 20
  ): Promise<{
    items: WorkoutSummary[];
    next_cursor: string | null;
  }> {
    try {
      // ⚠️ LOCKED RULE: Always use URLSearchParams for cursor (contains : and |)
      // Never use string concatenation - URLSearchParams handles encoding correctly
      const params = new URLSearchParams();
      if (cursor) {
        params.append('cursor', cursor);
      }
      params.append('limit', limit.toString());
      
      const res = await apiClient.get<{
        items: WorkoutSummary[];
        next_cursor: string | null;
      }>(`/workouts?${params.toString()}`);
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error getting history:', error);
      throw error;
    }
  },

  /**
   * Get workout detail by ID.
   * GET /api/v1/workouts/{id}
   * 
   * @param workoutId Workout UUID
   * @returns Full workout with exercises and sets
   */
  async getWorkoutDetail(workoutId: string): Promise<WorkoutOut> {
    try {
      const res = await apiClient.get<WorkoutOut>(
        `/workouts/${workoutId}`
      );
      return res.data;
    } catch (error) {
      console.error('[workoutApi] Error getting workout detail:', error);
      throw error;
    }
  },

  /**
   * Get AI-generated summary for a workout (AI Summaries & Trends).
   * GET /api/v1/workouts/{id}/ai-summary
   * Returns cached summary if available; otherwise generates via LLM.
   */
  async getWorkoutAISummary(workoutId: string): Promise<{ summary: string }> {
    const res = await apiClient.get<{ summary: string }>(
      `/workouts/${workoutId}/ai-summary`
    );
    return res.data;
  },
};
