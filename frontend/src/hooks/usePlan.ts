/**
 * usePlan: current plan + this week's adjustment, create, updatePreferences, history (Phase 2 Week 7).
 * Handles 404 when no plan (noPlan = true). Auto-adjust toggle: 403 for free users.
 */
import { useState, useCallback, useEffect } from 'react';
import {
  planApi,
  type Plan,
  type PlanAdjustment,
  type PlanCurrentResponse,
  type PlanPreferencesUpdate,
} from '../services/api/plan.api';

export function usePlan(isOnline: boolean) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [noPlan, setNoPlan] = useState(false);
  const [current, setCurrent] = useState<PlanCurrentResponse | null>(null);
  const [history, setHistory] = useState<PlanAdjustment[]>([]);
  const [updatingPreferences, setUpdatingPreferences] = useState(false);
  const [creating, setCreating] = useState(false);

  const fetchCurrent = useCallback(async () => {
    if (!isOnline) return;
    setLoading(true);
    setError(null);
    setNoPlan(false);
    try {
      const data = await planApi.getCurrent();
      setCurrent(data);
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: string } } };
      if (ax.response?.status === 404) {
        setNoPlan(true);
        setCurrent(null);
      } else {
        const message =
          typeof ax.response?.data?.detail === 'string'
            ? ax.response.data.detail
            : err instanceof Error
              ? err.message
              : 'Failed to load plan';
        setError(message);
        setCurrent(null);
      }
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  const fetchHistory = useCallback(async () => {
    if (!isOnline) return;
    try {
      const data = await planApi.getHistory(12);
      setHistory(data);
    } catch {
      setHistory([]);
    }
  }, [isOnline]);

  const fetchAll = useCallback(async () => {
    if (!isOnline) return;
    setLoading(true);
    setError(null);
    setNoPlan(false);
    try {
      const [currentRes, historyRes] = await Promise.all([
        planApi.getCurrent().catch((err: unknown) => {
          const ax = err as { response?: { status?: number } };
          if (ax.response?.status === 404) return null;
          throw err;
        }),
        planApi.getHistory(12),
      ]);
      setCurrent(currentRes);
      setNoPlan(!currentRes);
      setHistory(historyRes ?? []);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to load plan';
      setError(message);
      setCurrent(null);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const refetch = useCallback(() => fetchAll(), [fetchAll]);

  const createPlan = useCallback(async (): Promise<Plan | null> => {
    if (!isOnline) return null;
    setCreating(true);
    setError(null);
    try {
      const plan = await planApi.create();
      await fetchAll();
      return plan;
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to create plan';
      setError(message);
      return null;
    } finally {
      setCreating(false);
    }
  }, [isOnline, fetchAll]);

  const updatePreferences = useCallback(
    async (body: PlanPreferencesUpdate): Promise<Plan | null> => {
      if (!isOnline) return null;
      setUpdatingPreferences(true);
      setError(null);
      try {
        const plan = await planApi.updatePreferences(body);
        await fetchCurrent();
        await fetchHistory();
        return plan;
      } catch (err: unknown) {
        const ax = err as { response?: { status?: number; data?: { detail?: string } } };
        const message =
          ax.response?.status === 403 && typeof ax.response?.data?.detail === 'string'
            ? ax.response.data.detail
            : err instanceof Error
              ? err.message
              : 'Failed to update preferences';
        setError(message);
        return null;
      } finally {
        setUpdatingPreferences(false);
      }
    },
    [isOnline, fetchCurrent, fetchHistory]
  );

  return {
    plan: current?.plan ?? null,
    thisWeekAdjustment: current?.this_week_adjustment ?? null,
    history,
    loading,
    error,
    noPlan,
    refetch,
    createPlan,
    updatePreferences,
    updatingPreferences,
    creating,
  };
}
