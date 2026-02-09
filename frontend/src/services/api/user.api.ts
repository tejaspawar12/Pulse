/**
 * User API methods.
 * CRITICAL: Always normalize booleans to prevent React Native bridge errors.
 */
import { apiClient } from './client';
import { UserStatusOut, LastPerformance } from '../../types/workout.types';
import { User } from '../../types/user.types';
import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Normalize value to proper boolean type.
 * CRITICAL: React Native bridge requires actual booleans, not strings.
 */
const normalizeBoolean = (value: any): boolean => {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    const lower = value.toLowerCase().trim();
    return lower === 'true' || lower === '1' || lower === 'yes';
  }
  if (value === null || value === undefined) return false;
  return Boolean(value);
};

/**
 * Request deduplication for getStatus().
 * Prevents duplicate API calls within a short time window (2 seconds).
 */
let pendingGetStatusRequest: Promise<UserStatusOut> | null = null;
let lastGetStatusTime: number = 0;
const GET_STATUS_DEDUP_WINDOW_MS = 2000; // 2 seconds

/**
 * Cache for previous performance data.
 * Key format: `${userId}:${exerciseId}` to prevent cache collisions in multi-user scenarios.
 * Value: { data: LastPerformance | null, timestamp: number }
 */
const lastPerformanceCache = new Map<string, { data: LastPerformance | null; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export const userApi = {
  /**
   * Get user status.
   * GET /api/v1/me/status
   * CRITICAL: Returns safe default with proper booleans on error.
   * 
   * Request deduplication: If called multiple times within 2 seconds,
   * returns the same promise to prevent duplicate network requests.
   */
  async getStatus(): Promise<UserStatusOut> {
    const now = Date.now();
    
    // If there's a pending request and it's within the dedup window, return it
    if (pendingGetStatusRequest && (now - lastGetStatusTime) < GET_STATUS_DEDUP_WINDOW_MS) {
      return pendingGetStatusRequest;
    }
    
    // Create new request
    lastGetStatusTime = now;
    pendingGetStatusRequest = (async () => {
      try {
        const res = await apiClient.get<UserStatusOut>('/me/status');
        const data = res.data;
        
        // CRITICAL: Normalize ALL boolean fields to ensure proper booleans
        const normalized: UserStatusOut = {
          active_workout: data.active_workout,
          today_worked_out: normalizeBoolean(data.today_worked_out),
          last_30_days: (data.last_30_days ?? []).map(day => ({
            date: day.date,
            worked_out: normalizeBoolean(day.worked_out),
          })),
        };
        
        return normalized;
      } catch (error) {
        // CRITICAL: On error, return safe default with PROPER BOOLEANS (not strings)
        console.error('[userApi] Error getting status, returning safe default');
        
        const safeDefault: UserStatusOut = {
          active_workout: null,
          today_worked_out: false,
          last_30_days: [],
        };
        
        return safeDefault;
      } finally {
        // Clear pending request after completion (with small delay to allow concurrent calls to reuse)
        setTimeout(() => {
          pendingGetStatusRequest = null;
        }, GET_STATUS_DEDUP_WINDOW_MS);
      }
    })();
    
    return pendingGetStatusRequest;
  },

  /**
   * Get current user profile.
   * GET /api/v1/users/me
   */
  async getProfile(): Promise<User> {
    try {
      const res = await apiClient.get<User>('/users/me');
      return res.data;
    } catch (error) {
      console.error('[userApi] Error getting profile:', error);
      throw error;
    }
  },

  /**
   * Update user settings.
   * PATCH /api/v1/users/me
   */
  async updateSettings(data: {
    units?: 'kg' | 'lb';
    timezone?: string;
    default_rest_timer_seconds?: number;
    weight_kg?: number | null;
    height_cm?: number | null;
    date_of_birth?: string | null; // YYYY-MM-DD
    gender?: string | null; // male, female, other, prefer_not_say
  }): Promise<User> {
    try {
      const res = await apiClient.patch<User>('/users/me', data);
      return res.data;
    } catch (error) {
      console.error('[userApi] Error updating settings:', error);
      throw error;
    }
  },

  /**
   * Get last logged performance for exercise.
   * GET /api/v1/users/me/exercises/{id}/last-performance
   * 
   * Uses cache to prevent duplicate API calls. Cache is keyed by userId:exerciseId
   * to prevent collisions in multi-user scenarios.
   * 
   * @param exerciseId Exercise library UUID
   * @returns Last performance data or null if never logged
   */
  async getLastPerformance(exerciseId: string): Promise<LastPerformance | null> {
    // Get userId from AsyncStorage (same way API client does)
    const userId = await AsyncStorage.getItem('dev_user_id');
    if (!userId) {
      // If no userId, skip cache and make direct API call
      try {
        const res = await apiClient.get<LastPerformance>(
          `/users/me/exercises/${exerciseId}/last-performance`
        );
        return res.data;
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null;
        }
        console.error('[userApi] Error getting last performance:', error);
        throw error;
      }
    }

    // Create cache key: userId:exerciseId
    const cacheKey = `${userId}:${exerciseId}`;

    // Check cache first
    const cached = lastPerformanceCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp) < CACHE_TTL_MS) {
      return cached.data;
    }

    try {
      const res = await apiClient.get<LastPerformance>(
        `/users/me/exercises/${exerciseId}/last-performance`
      );
      const data = res.data;

      // Cache result
      lastPerformanceCache.set(cacheKey, { data, timestamp: Date.now() });
      return data;
    } catch (error: any) {
      // Return null if 404 (never logged)
      if (error.response?.status === 404) {
        // Cache null result too (prevents repeated 404 calls)
        lastPerformanceCache.set(cacheKey, { data: null, timestamp: Date.now() });
        return null;
      }
      console.error('[userApi] Error getting last performance:', error);
      throw error;
    }
  },

  /**
   * Clear all previous performance cache.
   * Useful after finishing workout or any mutation that might change performance data.
   */
  clearLastPerformanceCache(): void {
    lastPerformanceCache.clear();
  },

  /**
   * Clear cache for specific exercise.
   * Useful after adding/editing/deleting sets for a specific exercise.
   * 
   * @param exerciseId Exercise library UUID
   */
  clearLastPerformanceCacheForExercise(exerciseId: string): Promise<void> {
    return (async () => {
      const userId = await AsyncStorage.getItem('dev_user_id');
      if (userId) {
        const cacheKey = `${userId}:${exerciseId}`;
        lastPerformanceCache.delete(cacheKey);
      }
    })();
  },
};
