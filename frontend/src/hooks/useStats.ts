import { useState, useEffect, useCallback } from 'react';
import { statsApi, StatsSummary, StreakData, VolumeData } from '../services/api/stats.api';

export type PeriodDays = 7 | 30 | 90;

export function useStats(periodDays: PeriodDays) {
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [streak, setStreak] = useState<StreakData | null>(null);
  const [volume, setVolume] = useState<VolumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const groupBy = periodDays === 7 ? 'day' : 'week';

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, streakRes, volumeRes] = await Promise.all([
        statsApi.getSummary(periodDays),
        statsApi.getStreak(),
        statsApi.getVolume(periodDays, groupBy),
      ]);
      setSummary(summaryRes);
      setStreak(streakRes);
      setVolume(volumeRes);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load stats';
      setError(message);
      setSummary(null);
      setStreak(null);
      setVolume(null);
    } finally {
      setLoading(false);
    }
  }, [periodDays, groupBy]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return { summary, streak, volume, loading, error, refetch: fetchAll };
}
