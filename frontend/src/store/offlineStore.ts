/**
 * Offline read-only cache store. Phase 2 Week 4.
 * Persists to AsyncStorage so cache survives app restarts.
 * Clear on logout to avoid leaking data between users.
 */
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { WorkoutSummary, WorkoutOut } from '../types/workout.types';
import type { StatsSummary } from '../services/api/stats.api';

const CACHE_VERSION = 1;
const MAX_CACHED_WORKOUT_DETAILS = 30;
const OFFLINE_CACHE_KEY = 'offline-cache';

export interface OfflineState {
  cacheVersion: number;
  cachedHistory: WorkoutSummary[];
  cachedWorkoutDetails: Record<string, WorkoutOut>;
  cachedStatsSummary7: StatsSummary | null;
  lastCacheUpdate: Record<string, number>;

  setCachedHistory: (data: WorkoutSummary[]) => void;
  setCachedWorkoutDetail: (id: string, data: WorkoutOut) => void;
  setCachedStatsSummary7: (data: StatsSummary | null) => void;
  clearCache: () => void;
}

const getDefaultState = (): Omit<OfflineState, 'setCachedHistory' | 'setCachedWorkoutDetail' | 'setCachedStatsSummary7' | 'clearCache'> => ({
  cacheVersion: CACHE_VERSION,
  cachedHistory: [],
  cachedWorkoutDetails: {},
  cachedStatsSummary7: null,
  lastCacheUpdate: {},
});

function evictOldestWorkoutDetails(
  details: Record<string, WorkoutOut>,
  updates: Record<string, number>
): { details: Record<string, WorkoutOut>; updates: Record<string, number> } {
  const keys = Object.keys(details);
  if (keys.length <= MAX_CACHED_WORKOUT_DETAILS) {
    return { details, updates };
  }
  const sorted = keys
    .map((id) => ({ id, ts: updates[`workout_${id}`] ?? 0 }))
    .sort((a, b) => a.ts - b.ts);
  const toRemove = sorted.slice(0, keys.length - MAX_CACHED_WORKOUT_DETAILS).map((x) => x.id);
  const nextDetails = { ...details };
  const nextUpdates = { ...updates };
  toRemove.forEach((id) => {
    delete nextDetails[id];
    delete nextUpdates[`workout_${id}`];
  });
  return { details: nextDetails, updates: nextUpdates };
}

export const useOfflineStore = create<OfflineState>()(
  persist(
    (set, get) => ({
      ...getDefaultState(),

      setCachedHistory: (data) =>
        set((state) => ({
          cachedHistory: data,
          lastCacheUpdate: { ...state.lastCacheUpdate, history: Date.now() },
        })),

      setCachedWorkoutDetail: (id, data) =>
        set((state) => {
          const nextDetails = { ...state.cachedWorkoutDetails, [id]: data };
          const nextUpdates = {
            ...state.lastCacheUpdate,
            [`workout_${id}`]: Date.now(),
          };
          const { details, updates } = evictOldestWorkoutDetails(nextDetails, nextUpdates);
          return {
            cachedWorkoutDetails: details,
            lastCacheUpdate: updates,
          };
        }),

      setCachedStatsSummary7: (data) =>
        set((state) => ({
          cachedStatsSummary7: data,
          lastCacheUpdate: { ...state.lastCacheUpdate, statsSummary7: Date.now() },
        })),

      clearCache: () => set(getDefaultState()),
    }),
    {
      name: OFFLINE_CACHE_KEY,
      storage: createJSONStorage(() => AsyncStorage),
      onRehydrateStorage: () => (state) => {
        if (state?.cacheVersion !== CACHE_VERSION) {
          useOfflineStore.getState().clearCache();
        }
      },
    }
  )
);
