/**
 * Phase 3 — AI API: GET /ai/insights, GET /ai/usage.
 */
import { apiClient } from './client';

export interface NextWorkoutItem {
  exercise_name: string;
  sets_reps_guidance: string;
}

export interface AIInsights {
  summary: string;
  strengths: string[];
  gaps: string[];
  next_workout: NextWorkoutItem[];
  progression_rule: string;
  request_id?: string;
}

export interface AIUsage {
  insights_remaining_today: number;
  insights_limit_per_day: number;
  request_id?: string;
}

export const aiApi = {
  getInsights: async (days: 7 | 30): Promise<AIInsights> => {
    const res = await apiClient.get<AIInsights>('/ai/insights', { params: { days } });
    return res.data;
  },
  getUsage: async (): Promise<AIUsage> => {
    const res = await apiClient.get<AIUsage>('/ai/usage');
    return res.data;
  },
};
