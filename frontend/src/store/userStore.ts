/**
 * Zustand store for user state.
 * 
 * CRITICAL: NO persist middleware - causes React Native bridge errors.
 * - userStatus is NEVER persisted (fresh from API each app start)
 * - devUserId is persisted manually in App.tsx (no middleware needed)
 * - authToken is stored in SecureStore (encrypted, secure)
 */
import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { secureStorage } from '../utils/secureStorage';
import { UserStatusOut } from '../types/workout.types';
import { User } from '../types/user.types';

/**
 * Normalize value to proper boolean type.
 * CRITICAL: React Native bridge requires actual booleans, not strings.
 * This is a defensive layer in case API normalization missed something.
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

/** Refresh token key (SecureStore only, not in Zustand state). */
const REFRESH_TOKEN_KEY = 'fitnesscoach.refresh_token';

/** Save refresh token (SecureStore on native, localStorage on web). */
export async function saveRefreshToken(token: string): Promise<void> {
  await secureStorage.setItemAsync(REFRESH_TOKEN_KEY, token);
}

/** Get refresh token. */
export async function getRefreshToken(): Promise<string | null> {
  return secureStorage.getItemAsync(REFRESH_TOKEN_KEY);
}

/** Clear refresh token. */
export async function clearRefreshToken(): Promise<void> {
  await secureStorage.deleteItemAsync(REFRESH_TOKEN_KEY);
}

interface UserState {
  // Auth state
  isAuthenticated: boolean;
  authToken: string | null;
  authLoading: boolean;

  // Dev auth
  devUserId: string | null;

  // User status
  userStatus: UserStatusOut | null;

  // User profile
  userProfile: User | null;

  // Phase 2 Week 1 — email verification / entitlement
  emailVerified: boolean;
  entitlement: 'free' | 'pro';
  proTrialEndsAt: string | null;

  // Auth actions
  login: (token: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  setAuthToken: (token: string | null) => Promise<void>;
  initAuth: () => Promise<void>;
  setEmailVerified: (verified: boolean, trialEndsAt?: string | null) => void;

  // Existing actions
  setDevUserId: (userId: string) => Promise<void>;
  setUserStatus: (status: UserStatusOut) => void;
  setUserProfile: (profile: User) => void;
  clearDevUserId: () => void;
}

export const useUserStore = create<UserState>()((set) => ({
  // Auth state
  isAuthenticated: false,
  authToken: null,
  authLoading: true,

  devUserId: null,
  userStatus: null,
  userProfile: null,

  emailVerified: false,
  entitlement: 'free',
  proTrialEndsAt: null,

  login: async (token, user) => {
    await secureStorage.setItemAsync('fitnesscoach.auth_token', token);
    const emailVerified = user.email_verified ?? false;
    const entitlement = (user.entitlement ?? 'free') as 'free' | 'pro';
    const proTrialEndsAt = user.pro_trial_ends_at ?? null;
    set({
      isAuthenticated: true,
      authToken: token,
      userProfile: user,
      emailVerified,
      entitlement,
      proTrialEndsAt,
    });
  },

  logout: async () => {
    try {
      await secureStorage.deleteItemAsync('fitnesscoach.auth_token');
    } catch (error) {
      console.warn('Error clearing auth token:', error);
    }
    try {
      await secureStorage.deleteItemAsync(REFRESH_TOKEN_KEY);
    } catch (error) {
      console.warn('Error clearing refresh token:', error);
    }

    // Clear workout store
    try {
      const { useWorkoutStore } = require('./workoutStore');
      useWorkoutStore.getState().clearActiveWorkout();
      useWorkoutStore.getState().setLoaded(false);
    } catch (_e) {
      // Ignore if workoutStore not available (e.g. circular load)
    }

    // Clear offline cache (Phase 2 Week 4) so next user doesn't see previous user's data
    try {
      const { useOfflineStore } = require('./offlineStore');
      useOfflineStore.getState().clearCache();
    } catch (_e) {
      // Ignore if offlineStore not available
    }

    set({
      isAuthenticated: false,
      authToken: null,
      userProfile: null,
      userStatus: null,
      authLoading: false,
      emailVerified: false,
      entitlement: 'free',
      proTrialEndsAt: null,
    });
  },

  setEmailVerified: (verified, trialEndsAt) => {
    set((state) => ({
      emailVerified: verified,
      ...(trialEndsAt != null && { proTrialEndsAt: trialEndsAt }),
      // Banner checks userProfile?.email_verified — keep it in sync so banner hides after verify
      userProfile: state.userProfile
        ? {
            ...state.userProfile,
            email_verified: verified,
            ...(trialEndsAt != null && { pro_trial_ends_at: trialEndsAt }),
          }
        : state.userProfile,
    }));
  },

  setAuthToken: async (token) => {
    if (token) {
      await secureStorage.setItemAsync('fitnesscoach.auth_token', token);
    } else {
      try {
        await secureStorage.deleteItemAsync('fitnesscoach.auth_token');
      } catch (error) {
        // Ignore errors
      }
    }
    set({ authToken: token, isAuthenticated: !!token });
  },

  initAuth: async () => {
    // ⚠️ CRITICAL: Set loading to prevent login flash
    set({ authLoading: true });
    
    try {
      // ⚠️ CRITICAL: Read token from secure storage (only during bootstrap)
      // ✅ Use namespaced key: 'fitnesscoach.auth_token'
      const token = await secureStorage.getItemAsync('fitnesscoach.auth_token');
      
      if (!token) {
        // No token - not authenticated
        set({ 
          isAuthenticated: false, 
          authToken: null,
        });
        return;
      }

      // ⚠️ CRITICAL BUG FIX: Set token in state BEFORE calling getProfile()
      // Interceptor reads from Zustand state, so token must be set first
      // Otherwise getProfile() will fail with 401 (no Bearer token attached)
      // Note: We don't set isAuthenticated: true here - only after profile verification succeeds
      // This keeps isAuthenticated tied to verification, not just token presence
      set({ authToken: token });

      // Verify token by fetching user profile
      try {
        const { userApi } = await import('../services/api/user.api');
        const profile = await userApi.getProfile();
        
        set({
          isAuthenticated: true,
          authToken: token,
          userProfile: profile,
          emailVerified: profile.email_verified ?? false,
          entitlement: (profile.entitlement ?? 'free') as 'free' | 'pro',
          proTrialEndsAt: profile.pro_trial_ends_at ?? null,
        });
      } catch (error) {
        // Token invalid - clear it
        try {
          await secureStorage.deleteItemAsync('fitnesscoach.auth_token');
        } catch (deleteError) {
          // Ignore delete errors
        }
        
        set({ 
          isAuthenticated: false, 
          authToken: null,
          userProfile: null,
        });
      }
    } catch (error) {
      console.error('Error during auth init:', error);
      // On error, assume not authenticated
      set({ 
        isAuthenticated: false, 
        authToken: null,
      });
    } finally {
      // ⚠️ CRITICAL: ALWAYS set authLoading to false in finally block
      // This ensures loading state is cleared even if SecureStore crashes, API fails, etc.
      set({ authLoading: false });
    }
  },

  setDevUserId: async (userId) => {
    set({ devUserId: userId });
    
    // Await AsyncStorage to avoid race conditions with API interceptor
    // Interceptor reads dev_user_id, so write must complete first
    const existing = await AsyncStorage.getItem('dev_user_id');
    if (existing !== userId) {
      await AsyncStorage.setItem('dev_user_id', userId);
    }
  },

  setUserStatus: (status) => {
    // CRITICAL: Normalize ALL boolean fields before storing
    // React Native bridge requires actual booleans, not strings
    // This is a defensive layer in case API normalization missed something
    
    const normalizedStatus: UserStatusOut = {
      active_workout: status.active_workout,
      today_worked_out: normalizeBoolean(status.today_worked_out),
      last_30_days: (status.last_30_days ?? []).map(day => ({
        date: day.date,
        worked_out: normalizeBoolean(day.worked_out),
      })),
    };
    
    // CRITICAL: Final type verification before setting state
    // React Native bridge requires strict type matching - no string booleans allowed
    const finalTodayWorkedOut = normalizeBoolean(normalizedStatus.today_worked_out);
    if (typeof finalTodayWorkedOut !== 'boolean') {
      console.error('CRITICAL: today_worked_out is not boolean after normalization, forcing to false');
      normalizedStatus.today_worked_out = false;
    }
    
    // Verify last_30_days array
    const verifiedLast30Days = normalizedStatus.last_30_days.map(day => {
      const verifiedWorkedOut = normalizeBoolean(day.worked_out);
      if (typeof verifiedWorkedOut !== 'boolean') {
        console.error('CRITICAL: worked_out in last_30_days is not boolean, forcing to false');
        return { date: day.date, worked_out: false };
      }
      return { date: day.date, worked_out: verifiedWorkedOut };
    });
    
    const finalStatus: UserStatusOut = {
      active_workout: normalizedStatus.active_workout,
      today_worked_out: finalTodayWorkedOut,
      last_30_days: verifiedLast30Days,
    };
    
    // CRITICAL: Wrap set() in try-catch to handle React Native bridge errors
    try {
      set({ userStatus: finalStatus });
    } catch (error) {
      console.error('Error setting userStatus in Zustand store:', error);
      // If setting fails, try with a minimal safe default
      try {
        const minimalSafe: UserStatusOut = {
          active_workout: null,
          today_worked_out: false,
          last_30_days: [],
        };
        set({ userStatus: minimalSafe });
      } catch (recoveryError) {
        console.error('Even minimal safe default failed, setting to null:', recoveryError);
        // Last resort: set to null to prevent app crash
        set({ userStatus: null });
      }
    }
  },

  setUserProfile: (profile) => {
    set({
      userProfile: profile,
      emailVerified: profile.email_verified ?? false,
      entitlement: (profile.entitlement ?? 'free') as 'free' | 'pro',
      proTrialEndsAt: profile.pro_trial_ends_at ?? null,
    });
  },

  clearDevUserId: () => {
    set({ devUserId: null });
    AsyncStorage.removeItem('dev_user_id');
  },
}));
