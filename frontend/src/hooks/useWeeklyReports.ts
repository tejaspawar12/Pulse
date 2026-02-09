/**
 * useWeeklyReports: fetch latest + history for weekly reports (Phase 2 Week 6).
 */
import { useState, useCallback, useEffect } from 'react';
import { reportsApi, type WeeklyReport } from '../services/api/reports.api';

export function useWeeklyReports(isOnline: boolean) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latest, setLatest] = useState<WeeklyReport | null>(null);
  const [history, setHistory] = useState<WeeklyReport[]>([]);

  const fetchAll = useCallback(async () => {
    if (!isOnline) return;
    setLoading(true);
    setError(null);
    try {
      const [latestRes, historyRes] = await Promise.all([
        reportsApi.getWeeklyLatest().catch(() => null),
        reportsApi.getWeeklyHistory(12),
      ]);
      setLatest(latestRes ?? null);
      setHistory(historyRes ?? []);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to load weekly reports';
      setError(message);
      setLatest(null);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const refetch = useCallback(() => fetchAll(), [fetchAll]);

  return {
    latest,
    history,
    loading,
    error,
    refetch,
  };
}
