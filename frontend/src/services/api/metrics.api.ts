/**
 * Phase 3 — Metrics API: GET /metrics/summary?days=7|30 (deterministic).
 */
import { apiClient } from './client';

export interface MetricsSummary {
  total_volume_kg: number;
  workouts_count: number;
  workouts_per_week: number;
  volume_by_muscle_group: Record<string, number>;
  pr_count: number;
  imbalance_hint: string | null;
  streak_days: number;
  period_days: number;
}

export const metricsApi = {
  getSummary: async (days: 7 | 30): Promise<MetricsSummary> => {
    const res = await apiClient.get<MetricsSummary>('/metrics/summary', { params: { days } });
    return res.data;
  },
};
