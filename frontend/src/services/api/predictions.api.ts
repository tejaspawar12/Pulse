/**
 * Predictions API: transformation timeline latest and history (Phase 2 Week 6).
 * Available to all authenticated users. Latest is computed on demand if none exists.
 */
import { apiClient } from './client';

export interface TransformationPrediction {
  id: string;
  user_id: string;
  computed_at: string;
  strength_gain_weeks: number | null;
  visible_change_weeks: number | null;
  next_milestone: string | null;
  next_milestone_weeks: number | null;
  weeks_delta: number | null;
  delta_reason: string | null;
  current_consistency_score: number | null;
  current_workouts_per_week: number | null;
  primary_goal: string | null; // strength, muscle, weight_loss, general
}

export const predictionsApi = {
  getTransformationLatest: async (
    recompute: boolean = false
  ): Promise<TransformationPrediction> => {
    const res = await apiClient.get<TransformationPrediction>(
      '/predictions/transformation/latest',
      { params: recompute ? { recompute: 'true' } : undefined }
    );
    return res.data;
  },
  getTransformationHistory: async (
    limit: number = 12
  ): Promise<TransformationPrediction[]> => {
    const res = await apiClient.get<TransformationPrediction[]>(
      '/predictions/transformation/history',
      { params: { limit } }
    );
    return res.data;
  },
};
