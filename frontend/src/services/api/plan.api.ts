/**
 * Plan API: current plan, create, preferences, adjustment history (Phase 2 Week 7).
 * Free user PATCH with auto_adjust_enabled=true → 403.
 */
import { apiClient } from './client';

export interface Plan {
  id: string;
  user_id: string;
  days_per_week: number | null;
  session_duration_target: number | null;
  split_type: string | null;
  volume_multiplier: number;
  progression_type: string | null;
  auto_adjust_enabled: boolean;
  deload_week_frequency: number | null;
  created_at: string;
  updated_at: string;
}

export interface PlanAdjustment {
  id: string;
  plan_id: string;
  user_id: string;
  week_start: string; // YYYY-MM-DD
  previous_days_per_week: number | null;
  new_days_per_week: number | null;
  previous_volume_multiplier: number | null;
  new_volume_multiplier: number | null;
  is_deload: boolean;
  trigger_reason: string | null;
  explanation_bullets: string[] | null;
  metrics_snapshot: MetricsSnapshot | null;
  explanation_title: string | null;
  applied_at: string;
}

export interface MetricsSnapshot {
  consistency_score?: number;
  burnout_risk?: string;
  momentum_trend?: string;
}

export interface PlanCurrentResponse {
  plan: Plan;
  this_week_adjustment: PlanAdjustment | null;
}

export interface PlanPreferencesUpdate {
  days_per_week?: number;
  session_duration_target?: number;
  split_type?: string;
  progression_type?: string;
  deload_week_frequency?: number;
  auto_adjust_enabled?: boolean;
}

export const planApi = {
  getCurrent: async (): Promise<PlanCurrentResponse> => {
    const res = await apiClient.get<PlanCurrentResponse>('/plan/current');
    return res.data;
  },

  create: async (): Promise<Plan> => {
    const res = await apiClient.post<Plan>('/plan/create');
    return res.data;
  },

  updatePreferences: async (body: PlanPreferencesUpdate): Promise<Plan> => {
    const res = await apiClient.patch<Plan>('/plan/preferences', body);
    return res.data;
  },

  getHistory: async (limit: number = 12): Promise<PlanAdjustment[]> => {
    const res = await apiClient.get<PlanAdjustment[]>('/plan/history', {
      params: { limit },
    });
    return res.data;
  },
};
