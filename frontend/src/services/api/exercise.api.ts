/**
 * Exercise API methods.
 */
import { apiClient } from './client';
import { Exercise, ExerciseList } from '../../types/exercise.types';

export interface ExerciseSearchParams {
  q?: string; // Search query (minimum 2 characters)
  muscle_group?: string; // Filter by muscle group
  equipment?: string; // Filter by equipment
  limit?: number; // Maximum results (default 50)
}

export const exerciseApi = {
  /**
   * Search exercises with fuzzy matching.
   * GET /api/v1/exercises
   * 
   * @param params Search parameters
   * @returns List of matching exercises
   */
  async search(params: ExerciseSearchParams = {}): Promise<Exercise[]> {
    try {
      const response = await apiClient.get<ExerciseList>('/exercises', {
        params: {
          q: params.q,
          muscle_group: params.muscle_group,
          equipment: params.equipment,
          limit: params.limit || 50,
        },
      });
      
      return response.data.exercises;
    } catch (error) {
      console.error('[exerciseApi] Error searching exercises:', error);
      return []; // Return empty array on error
    }
  },

  /**
   * Get recent exercises (used in last workouts).
   * GET /api/v1/exercises/recent
   * 
   * @param limit Maximum number of exercises (default 10)
   * @returns List of recent exercises
   */
  async getRecent(limit: number = 10): Promise<Exercise[]> {
    try {
      const response = await apiClient.get<ExerciseList>('/exercises/recent', {
        params: { limit },
      });
      
      return response.data.exercises;
    } catch (error) {
      console.error('[exerciseApi] Error getting recent exercises:', error);
      return []; // Return empty array on error
    }
  },
};
