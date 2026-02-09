/**
 * Reports API: weekly training report latest and history (Phase 2 Week 6).
 */
import { apiClient } from './client';

export interface WeeklyReport {
  id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  workouts_count: number | null;
  total_volume_kg: number | null;
  volume_delta_pct: number | null;
  prs_hit: number | null;
  avg_session_duration: number | null;
  primary_training_mistake_key: string | null;
  primary_training_mistake_label: string | null;
  weekly_focus_key: string | null;
  weekly_focus_label: string | null;
  positive_signal_key: string | null;
  positive_signal_label: string | null;
  positive_signal_reason: string | null;
  reasons: Array<{ reason_key: string; reason_label: string }> | null;
  narrative: string | null;
  narrative_source: string | null;
  status: string;
  generated_at: string;
}

export const reportsApi = {
  getWeeklyLatest: async (): Promise<WeeklyReport> => {
    const res = await apiClient.get<WeeklyReport>('/reports/weekly/latest');
    return res.data;
  },
  getWeeklyHistory: async (limit: number = 12): Promise<WeeklyReport[]> => {
    const res = await apiClient.get<WeeklyReport[]>('/reports/weekly/history', {
      params: { limit },
    });
    return res.data;
  },
};
