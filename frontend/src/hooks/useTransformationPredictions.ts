/**
 * useTransformationPredictions: fetch latest + history for timeline (Phase 2 Week 6).
 * Available to all authenticated users.
 */
import { useState, useCallback, useEffect } from 'react';
import {
  predictionsApi,
  type TransformationPrediction,
} from '../services/api/predictions.api';

export function useTransformationPredictions(isOnline: boolean) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latest, setLatest] = useState<TransformationPrediction | null>(null);
  const [history, setHistory] = useState<TransformationPrediction[]>([]);

  const fetchAll = useCallback(
    async (recompute: boolean = false) => {
      if (!isOnline) return;
      setLoading(true);
      setError(null);
      try {
        const [latestRes, historyRes] = await Promise.all([
          predictionsApi.getTransformationLatest(recompute),
          predictionsApi.getTransformationHistory(12),
        ]);
        setLatest(latestRes);
        setHistory(historyRes ?? []);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Failed to load timeline';
        setError(message);
        setLatest(null);
        setHistory([]);
      } finally {
        setLoading(false);
      }
    },
    [isOnline]
  );

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const refetch = useCallback(
    (recompute: boolean = false) => fetchAll(recompute),
    [fetchAll]
  );

  return {
    latest,
    history,
    loading,
    error,
    refetch,
  };
}
