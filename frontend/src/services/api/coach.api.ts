/**
 * Coach API: today's message, respond, status, metrics (Phase 2 Week 5 Day 5).
 */
import { apiClient } from './client';

export type CoachSource = 'ai' | 'free_tier' | 'unavailable';

export interface CoachTodayMessage {
  source: CoachSource;
  coach_message?: string;
  quick_replies?: string[];
  one_action_step?: string;
  is_free_tier?: boolean;
  retry_after_seconds?: number;
  generated_at?: string;
  model_id?: string;
  ai_lite_used?: boolean;
}

export interface CoachStatus {
  consistency_score: number | null;
  momentum_trend: string | null;
  dropout_risk: string | null;
  burnout_risk: string | null;
  primary_training_mistake_key: string | null;
  primary_training_mistake_label: string | null;
  weekly_focus_key: string | null;
  weekly_focus_label: string | null;
}

export interface CoachMetricsDay {
  metrics_date: string;
  consistency_score: number | null;
  dropout_risk: string | null;
  burnout_risk: string | null;
  momentum_trend: string | null;
  adherence_type: string | null;
  workouts_last_7_days: number | null;
  workouts_last_14_days: number | null;
  primary_training_mistake_key: string | null;
  weekly_focus_key: string | null;
  reasons: Array<{ reason_key: string; reason_label: string }> | null;
}

export interface CoachChatMessage {
  role: 'user' | 'assistant';
  content: string;
  created_at: string | null;
}

/** Coach profile: goal and preferences (used by timeline, coach, plan). */
export interface CoachProfile {
  primary_goal: string | null; // strength, muscle, weight_loss, general
  experience_level: string | null;
  target_days_per_week: number | null;
  target_session_minutes: number | null;
}

export type PrimaryGoalValue = 'strength' | 'muscle' | 'weight_loss' | 'general';

export const coachApi = {
  getProfile: async (): Promise<CoachProfile> => {
    const res = await apiClient.get<CoachProfile>('/coach/profile');
    return res.data;
  },

  updateProfile: async (data: { primary_goal?: PrimaryGoalValue | null }): Promise<CoachProfile> => {
    const res = await apiClient.patch<CoachProfile>('/coach/profile', data);
    return res.data;
  },

  getTodayMessage: async (): Promise<CoachTodayMessage> => {
    const res = await apiClient.get<CoachTodayMessage>('/coach/today');
    return res.data;
  },

  getChatHistory: async (limit: number = 50): Promise<CoachChatMessage[]> => {
    const res = await apiClient.get<CoachChatMessage[]>('/coach/chat', { params: { limit } });
    return res.data;
  },

  sendChatMessage: async (message: string): Promise<{ reply: string }> => {
    // Coach LLM can take 15–60s; use longer timeout so web and native both succeed
    const res = await apiClient.post<{ reply: string }>('/coach/chat', { message }, { timeout: 60000 });
    return res.data;
  },

  respondToMessage: async (replyText: string): Promise<void> => {
    await apiClient.post('/coach/respond', { reply_text: replyText });
  },

  getStatus: async (): Promise<CoachStatus> => {
    const res = await apiClient.get<CoachStatus>('/coach/status');
    return res.data;
  },

  getMetrics: async (days: number = 30): Promise<CoachMetricsDay[]> => {
    const res = await apiClient.get<CoachMetricsDay[]>('/coach/metrics', { params: { days } });
    return res.data;
  },
};
