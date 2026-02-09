/**
 * Offline cache hook. Phase 2 Week 4.
 * Exposes isOnline (NetInfo, with isInternetReachable preferred) and cached data.
 * Use: when online fetch and set cache; when offline use cache only.
 */
import { useEffect, useState, useCallback } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { useOfflineStore } from '../store/offlineStore';
import type { WorkoutSummary, WorkoutOut } from '../types/workout.types';
import type { StatsSummary } from '../services/api/stats.api';

/**
 * Derive actual online state: prefer isInternetReachable; fallback to isConnected only when isInternetReachable is null.
 * Avoids false "online" on captive portals or bad Wi-Fi.
 */
function deriveIsOnline(state: NetInfoState | null): boolean {
  if (!state) return true;
  if (state.isInternetReachable === false) return false;
  if (state.isInternetReachable === true) return true;
  return state.isConnected === true;
}

export function useOfflineCache() {
  const [isOnline, setIsOnline] = useState(true);
  const cachedHistory = useOfflineStore((s) => s.cachedHistory);
  const cachedWorkoutDetails = useOfflineStore((s) => s.cachedWorkoutDetails);
  const cachedStatsSummary7 = useOfflineStore((s) => s.cachedStatsSummary7);
  const lastCacheUpdate = useOfflineStore((s) => s.lastCacheUpdate);
  const setCachedHistory = useOfflineStore((s) => s.setCachedHistory);
  const setCachedWorkoutDetail = useOfflineStore((s) => s.setCachedWorkoutDetail);
  const setCachedStatsSummary7 = useOfflineStore((s) => s.setCachedStatsSummary7);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOnline(deriveIsOnline(state));
    });
    return unsubscribe;
  }, []);

  const getCachedOrFetchHistory = useCallback(
    async (fetchFn: () => Promise<{ items: WorkoutSummary[] }>): Promise<WorkoutSummary[]> => {
      if (isOnline) {
        try {
          const res = await fetchFn();
          setCachedHistory(res.items);
          return res.items;
        } catch {
          return cachedHistory.length > 0 ? cachedHistory : [];
        }
      }
      return cachedHistory;
    },
    [isOnline, cachedHistory, setCachedHistory]
  );

  const getCachedOrFetchWorkoutDetail = useCallback(
    async (workoutId: string, fetchFn: () => Promise<WorkoutOut>): Promise<WorkoutOut | null> => {
      if (isOnline) {
        try {
          const data = await fetchFn();
          setCachedWorkoutDetail(workoutId, data);
          return data;
        } catch {
          return cachedWorkoutDetails[workoutId] ?? null;
        }
      }
      return cachedWorkoutDetails[workoutId] ?? null;
    },
    [isOnline, cachedWorkoutDetails, setCachedWorkoutDetail]
  );

  const getCachedOrFetchStatsSummary7 = useCallback(
    async (fetchFn: () => Promise<StatsSummary>): Promise<StatsSummary | null> => {
      if (isOnline) {
        try {
          const data = await fetchFn();
          setCachedStatsSummary7(data);
          return data;
        } catch {
          return cachedStatsSummary7;
        }
      }
      return cachedStatsSummary7;
    },
    [isOnline, cachedStatsSummary7, setCachedStatsSummary7]
  );

  return {
    isOnline,
    cachedHistory,
    cachedWorkoutDetails,
    cachedStatsSummary7,
    lastCacheUpdate,
    getCachedOrFetchHistory,
    getCachedOrFetchWorkoutDetail,
    getCachedOrFetchStatsSummary7,
  };
}
