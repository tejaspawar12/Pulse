/**
 * useCoach: fetch coach message + commitment for Log tab (Phase 2 Week 5 Day 5).
 * When offline, skip fetch; commit/respond disabled via isOnline in UI.
 */
import { useState, useCallback, useEffect } from 'react';
import { coachApi, type CoachTodayMessage, type CoachStatus } from '../services/api/coach.api';
import { accountabilityApi, type TodayCommitment } from '../services/api/accountability.api';

export interface CoachState {
  message: string | null;
  quickReplies: string[];
  oneActionStep: string | null;
  source: 'ai' | 'free_tier' | 'unavailable' | null;
  isFreeTier: boolean;
  retryAfterSeconds: number | null;
  primaryMistake: string | null;
  weeklyFocus: string | null;
}

export interface CommitmentState {
  commitment: TodayCommitment | null;
  committed: boolean;
  completed: boolean;
  status: TodayCommitment['status'];
}

export interface MetricsState {
  consistencyScore: number | null;
  momentumTrend: string | null;
  dropoutRisk: string | null;
  burnoutRisk: string | null;
  primaryMistakeKey: string | null;
  primaryMistakeLabel: string | null;
  weeklyFocusKey: string | null;
  weeklyFocusLabel: string | null;
  reasons: Array<{ reason_key: string; reason_label: string }> | null;
}

export function useCoach(isOnline: boolean) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coachMessage, setCoachMessage] = useState<CoachTodayMessage | null>(null);
  const [commitment, setCommitment] = useState<TodayCommitment | null>(null);
  const [status, setStatus] = useState<CoachStatus | null>(null);

  const fetchAll = useCallback(async () => {
    if (!isOnline) return;
    setLoading(true);
    setError(null);
    try {
      const [msgRes, commitRes, statusRes] = await Promise.all([
        coachApi.getTodayMessage(),
        accountabilityApi.getTodayCommitment(),
        coachApi.getStatus(),
      ]);
      setCoachMessage(msgRes);
      setCommitment(commitRes);
      setStatus(statusRes);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load coach data';
      setError(message);
      setCoachMessage(null);
      setCommitment(null);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const refetch = useCallback(() => {
    return fetchAll();
  }, [fetchAll]);

  const coach: CoachState = {
    message: coachMessage?.coach_message ?? null,
    quickReplies: coachMessage?.quick_replies ?? [],
    oneActionStep: coachMessage?.one_action_step ?? null,
    source: coachMessage?.source ?? null,
    isFreeTier: coachMessage?.is_free_tier ?? false,
    retryAfterSeconds: coachMessage?.retry_after_seconds ?? null,
    primaryMistake: status?.primary_training_mistake_label ?? null,
    weeklyFocus: status?.weekly_focus_label ?? null,
  };

  const commitmentState: CommitmentState = {
    commitment,
    committed: commitment?.status === 'yes',
    completed: commitment?.completed ?? false,
    status: commitment?.status ?? null,
  };

  const metrics: MetricsState = {
    consistencyScore: status?.consistency_score ?? null,
    momentumTrend: status?.momentum_trend ?? null,
    dropoutRisk: status?.dropout_risk ?? null,
    burnoutRisk: status?.burnout_risk ?? null,
    primaryMistakeKey: status?.primary_training_mistake_key ?? null,
    primaryMistakeLabel: status?.primary_training_mistake_label ?? null,
    weeklyFocusKey: status?.weekly_focus_key ?? null,
    weeklyFocusLabel: status?.weekly_focus_label ?? null,
    reasons: null,
  };

  // Load reasons from metrics if needed (status doesn't include reasons; we could add getMetrics(1) for "today" reasons)
  const [reasons, setReasons] = useState<Array<{ reason_key: string; reason_label: string }> | null>(null);
  useEffect(() => {
    if (!isOnline || !status) return;
    coachApi.getMetrics(1).then((list) => {
      const today = list?.[0];
      setReasons(today?.reasons ?? null);
    }).catch(() => setReasons(null));
  }, [isOnline, status?.consistency_score]);

  const metricsWithReasons: MetricsState = {
    ...metrics,
    reasons,
  };

  return {
    commitment: commitmentState,
    coach,
    metrics: metricsWithReasons,
    loading,
    error,
    refetch,
    rawMessage: coachMessage,
    rawCommitment: commitment,
  };
}
