/**
 * useCoachProfile: fetch coach profile (primary_goal) for display on Log, Coach, Plan.
 */
import { useState, useCallback, useEffect } from 'react';
import { coachApi } from '../services/api/coach.api';

function goalToLabel(goal: string | null | undefined): string {
  if (!goal) return '';
  const g = goal.toLowerCase();
  if (g === 'strength') return 'Strength';
  if (g === 'muscle') return 'Muscle gain';
  if (g === 'weight_loss') return 'Weight loss';
  if (g === 'general') return 'General fitness';
  return goal;
}

export function useCoachProfile(isOnline: boolean) {
  const [primaryGoal, setPrimaryGoal] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    if (!isOnline) return;
    setLoading(true);
    try {
      const profile = await coachApi.getProfile();
      setPrimaryGoal(profile.primary_goal ?? null);
    } catch {
      setPrimaryGoal(null);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const goalLabel = goalToLabel(primaryGoal);

  return {
    primaryGoal,
    goalLabel: goalLabel || null,
    loading,
    refetch: fetchProfile,
  };
}
