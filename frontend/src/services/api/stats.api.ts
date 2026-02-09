/**
 * Stats API: summary, streak, volume over time.
 */
import { apiClient } from './client';

export interface StatsSummary {
  period_days: number;
  total_workouts: number;
  total_volume_kg: number;
  total_sets: number;
  prs_hit: number;
  avg_workout_duration_minutes: number | null;
  most_trained_muscle: string | null;
}

export interface StreakData {
  current_streak_days: number;
  longest_streak_days: number;
  last_workout_date: string | null; // YYYY-MM-DD
}

export interface VolumeDataPoint {
  period_start: string; // YYYY-MM-DD
  period_end: string;
  total_volume_kg: number;
  workout_count: number;
}

export interface VolumeData {
  data: VolumeDataPoint[];
  period_days: number;
}

export const statsApi = {
  getSummary: async (days: number): Promise<StatsSummary> => {
    const res = await apiClient.get<StatsSummary>('/users/me/stats/summary', { params: { days } });
    return res.data;
  },
  getStreak: async (): Promise<StreakData> => {
    const res = await apiClient.get<StreakData>('/users/me/stats/streak');
    return res.data;
  },
  getVolume: async (days: number, groupBy: 'day' | 'week'): Promise<VolumeData> => {
    const res = await apiClient.get<VolumeData>('/users/me/stats/volume', {
      params: { days, group_by: groupBy },
    });
    return res.data;
  },
};
