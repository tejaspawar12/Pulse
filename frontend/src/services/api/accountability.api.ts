/**
 * Accountability API: today's commitment, commit, respond (Phase 2 Week 5 Day 5).
 */
import { apiClient } from './client';

export type CommitmentStatus = 'yes' | 'no' | 'rescheduled';

export interface TodayCommitment {
  commitment_date: string;
  status: CommitmentStatus | null;
  expected_time: string | null;
  expected_duration_minutes: number | null;
  rescheduled_to_date: string | null;
  rescheduled_to_time: string | null;
  completed: boolean;
  completed_at: string | null;
}

export interface CommitPayload {
  status: CommitmentStatus;
  expected_time?: string;
  expected_duration_minutes?: number;
  rescheduled_to_date?: string;
  rescheduled_to_time?: string;
}

export const accountabilityApi = {
  getTodayCommitment: async (): Promise<TodayCommitment> => {
    const res = await apiClient.get<TodayCommitment>('/accountability/today');
    return res.data;
  },

  commitToday: async (payload: CommitPayload): Promise<TodayCommitment> => {
    const res = await apiClient.post<TodayCommitment>('/accountability/commit', payload);
    return res.data;
  },

  respondToFollowUp: async (payload: { response_type?: string }): Promise<void> => {
    await apiClient.post('/accountability/respond', payload);
  },
};
