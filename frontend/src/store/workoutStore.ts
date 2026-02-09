/**
 * Zustand store for workout state.
 * Persists active workout for timer persistence.
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { WorkoutOut } from '../types/workout.types';

interface WorkoutState {
  // Full active workout (only loaded when needed, e.g., in LogScreen)
  activeWorkout: WorkoutOut | null;
  activeWorkoutLoaded: boolean;
  
  // Actions
  setActiveWorkout: (workout: WorkoutOut | null) => void;
  clearActiveWorkout: () => void;
  setLoaded: (loaded: boolean) => void;
  
  // Computed getters
  getStartTime: () => string | null;
}

export const useWorkoutStore = create<WorkoutState>()(
  persist(
    (set, get) => ({
      activeWorkout: null,
      activeWorkoutLoaded: false,

      setActiveWorkout: (workout) =>
        set({ activeWorkout: workout }),

      clearActiveWorkout: () =>
        set({ activeWorkout: null }),

      setLoaded: (loaded) =>
        set({ activeWorkoutLoaded: loaded }),

      // REMOVED: getActiveWorkoutSummary - use userStatus.active_workout instead
      // Backend already computes correct date using user timezone in /me/status
      // Don't recompute on client (would cause timezone bugs)

      getStartTime: (): string | null => {
        return get().activeWorkout?.start_time || null;
      },
    }),
    {
      name: 'workout-storage',
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist activeWorkout (not loaded flag)
      partialize: (state) => ({
        activeWorkout: state.activeWorkout,
      }),
    }
  )
);
