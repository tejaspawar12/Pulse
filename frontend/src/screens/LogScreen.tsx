/**
 * Log Screen - Main workout screen.
 * Shows "Start Workout" button or active workout session.
 */
import React, { useEffect, useLayoutEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, FlatList, RefreshControl, TextInput, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useWorkoutStore } from '../store/workoutStore';
import { useUserStore } from '../store/userStore';
import { OfflineBanner } from '../components/common/OfflineBanner';
import { GoalLabel } from '../components/common/GoalLabel';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { useCoach } from '../hooks/useCoach';
import { useTransformationPredictions } from '../hooks/useTransformationPredictions';
import { workoutApi } from '../services/api/workout.api';
import { TimelineSnapshotCard } from '../components/timeline/TimelineSnapshotCard';
import { StatusChipsRow } from '../components/log/StatusChipsRow';
import { isPortfolioMode } from '../config/constants';
import { WorkoutOut } from '../types/workout.types';
import { userApi } from '../services/api/user.api';
import { ExercisePicker } from '../components/exercise/ExercisePicker';
import { ExerciseCard } from '../components/workout/ExerciseCard';
import { AddSetForm } from '../components/workout/AddSetForm';
import { EditSetForm } from '../components/workout/EditSetForm';
import { FinishWorkoutModal } from '../components/workout/FinishWorkoutModal';
import { Timer } from '../components/common/Timer';
import { Exercise } from '../types/exercise.types';
import { WorkoutSet, CompletionStatus } from '../types/workout.types';
import { Alert } from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { addToQueue } from '../utils/offlineQueue';
import { useOfflineQueue } from '../hooks/useOfflineQueue';
import NetInfo from '@react-native-community/netinfo';
import { debounce } from '../utils/debounce';
import { useUserUnit } from '../hooks/useUserUnit';
import { convertWeightForDisplay, getUnitLabel } from '../utils/units';

const WORKOUT_ACTION_BAR_HEIGHT = 72; // Compact single-row action bar height

export const LogScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const { activeWorkout, activeWorkoutLoaded, setActiveWorkout, setLoaded, clearActiveWorkout } = useWorkoutStore();
  const { setUserStatus, userProfile } = useUserStore();
  const [loading, setLoading] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [exercisePickerVisible, setExercisePickerVisible] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [addSetFormVisible, setAddSetFormVisible] = React.useState(false);
  const [editSetFormVisible, setEditSetFormVisible] = React.useState(false);
  const [finishModalVisible, setFinishModalVisible] = React.useState(false);
  const [finishLoading, setFinishLoading] = React.useState(false);
  const [discardLoading, setDiscardLoading] = React.useState(false);
  const [selectedExerciseId, setSelectedExerciseId] = React.useState<string | null>(null);
  const [selectedSet, setSelectedSet] = React.useState<WorkoutSet | null>(null);
  
  // Name/notes editing state
  const [workoutName, setWorkoutName] = React.useState<string>('');
  const [workoutNotes, setWorkoutNotes] = React.useState<string>('');
  const [showNotes, setShowNotes] = React.useState(false);
  const [updatingName, setUpdatingName] = React.useState(false);
  const [updatingNotes, setUpdatingNotes] = React.useState(false);
  
  // ⚠️ CRITICAL: Use ref to avoid stale closure in debounced functions
  const latestWorkoutRef = React.useRef<WorkoutOut | null>(null);
  
  // Offline queue hook
  const { processQueue, queueLength } = useOfflineQueue();
  const { isOnline } = useOfflineCache();
  const units = useUserUnit();
  const unitLabel = getUnitLabel(units);
  const { metrics, loading: coachLoading, error: coachError, refetch: refetchCoach } = useCoach(isOnline);
  const { latest: timelineLatest } = useTransformationPredictions(isOnline);

  // Hevy-like: when workout is active, show Finish in header; hide tab bar is handled in AppNavigator
  useLayoutEffect(() => {
    if (activeWorkout) {
      navigation.setOptions({
        title: 'Log Workout',
        headerRight: () => (
          <TouchableOpacity
            onPress={() => setFinishModalVisible(true)}
            disabled={loading || finishLoading || discardLoading || !isOnline}
            style={styles.headerFinishButton}
          >
            <Text style={[styles.headerFinishText, (loading || finishLoading || discardLoading || !isOnline) && styles.headerFinishDisabled]}>
              Finish
            </Text>
          </TouchableOpacity>
        ),
      });
    } else {
      navigation.setOptions({ headerRight: undefined });
    }
  }, [activeWorkout, navigation, loading, finishLoading, discardLoading, isOnline]);

  // Refetch coach when Log tab gains focus (e.g. after returning from Profile / verifying email)
  useFocusEffect(
    React.useCallback(() => {
      if (isOnline) refetchCoach();
    }, [isOnline, refetchCoach])
  );

  // Load full active workout only when entering LogScreen (for workout session details)
  // Active workout bar uses userStatus.active_workout from /me/status (loaded in App.tsx)
  // FIXED: Removed redundant getStatus() call - App.tsx already loads status on startup
  // Status is kept in sync via Zustand store, no need to reload here
  useEffect(() => {
    // Guard: Only load if not already loaded
    if (activeWorkoutLoaded) return;
    
    const loadActiveWorkout = async () => {
      try {
        setLoading(true);
        const workout = await workoutApi.getActive();
        setActiveWorkout(workout);
        setLoaded(true);

        // NOTE: Removed redundant userApi.getStatus() call here
        // App.tsx already loads status on startup and updates Zustand store
        // ActiveWorkoutBar reads from userStatus.active_workout which is already loaded
        // If we need fresh status after loading workout, Zustand store will have it
      } catch (error) {
        console.error('Error loading active workout:', error);
        setLoaded(true);
      } finally {
        setLoading(false);
      }
    };

    loadActiveWorkout();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // Zustand setters (setActiveWorkout, setLoaded) are stable and don't need to be in deps
    // Only activeWorkoutLoaded needs to trigger re-run
  }, [activeWorkoutLoaded]);

  // Update local state when active workout changes
  useEffect(() => {
    if (activeWorkout) {
      setWorkoutName(activeWorkout.name || '');
      setWorkoutNotes(activeWorkout.notes || '');
      latestWorkoutRef.current = activeWorkout; // Keep ref updated
    }
  }, [activeWorkout]);

  // ⚠️ CRITICAL: Debounce based on stable workoutId, use ref for latest workout
  // This prevents stale closure bug where debounced function references old activeWorkout
  // ⚠️ FIX: Return debounced function directly (not wrapped object) so cancel() works
  const debouncedUpdateName = React.useMemo(
    () => {
      const fn = debounce(async (workoutId: string, name: string) => {
        // Get latest workout from ref (not closure)
        const currentWorkout = latestWorkoutRef.current;
        if (!currentWorkout || currentWorkout.id !== workoutId) return;
        
        // Only update if value changed
        if (name === currentWorkout.name) {
          setUpdatingName(false);
          return;
        }
        
        try {
          setUpdatingName(true);
          const updated = await workoutApi.updateWorkout(workoutId, { name: name || undefined });
          // Clear previous performance cache (workout update may affect performance data)
          userApi.clearLastPerformanceCache();
          // Update local workout state
          setActiveWorkout(updated);
          latestWorkoutRef.current = updated; // Update ref
        } catch (error: any) {
          console.error('Error updating workout name:', error);
          // Revert to previous value on error
          const prevName = currentWorkout.name || '';
          setWorkoutName(prevName);
          Alert.alert('Error', 'Failed to update workout name. Please try again.');
        } finally {
          setUpdatingName(false);
        }
      }, 800);
      
      // Return debounced function directly (has .cancel() method)
      return fn;
    },
    [] // Empty deps - debounced function is stable
  );

  const debouncedUpdateNotes = React.useMemo(
    () => {
      const fn = debounce(async (workoutId: string, notes: string) => {
        // Get latest workout from ref (not closure)
        const currentWorkout = latestWorkoutRef.current;
        if (!currentWorkout || currentWorkout.id !== workoutId) return;
        
        // Only update if value changed
        if (notes === currentWorkout.notes) {
          setUpdatingNotes(false);
          return;
        }
        
        try {
          setUpdatingNotes(true);
          const updated = await workoutApi.updateWorkout(workoutId, { notes: notes || undefined });
          // Clear previous performance cache (workout update may affect performance data)
          userApi.clearLastPerformanceCache();
          // Update local workout state
          setActiveWorkout(updated);
          latestWorkoutRef.current = updated; // Update ref
        } catch (error: any) {
          console.error('Error updating workout notes:', error);
          // Revert to previous value on error
          const prevNotes = currentWorkout.notes || '';
          setWorkoutNotes(prevNotes);
          Alert.alert('Error', 'Failed to update workout notes. Please try again.');
        } finally {
          setUpdatingNotes(false);
        }
      }, 800);
      
      // Return debounced function directly (has .cancel() method)
      return fn;
    },
    [] // Empty deps - debounced function is stable
  );

  // ⚠️ CRITICAL: Cleanup on unmount to prevent setting state on unmounted screen
  useEffect(() => {
    return () => {
      // Cancel pending debounced calls on unmount
      // Works for both custom debounce (has .cancel()) and lodash (has .cancel())
      debouncedUpdateName.cancel?.();
      debouncedUpdateNotes.cancel?.();
    };
  }, [debouncedUpdateName, debouncedUpdateNotes]);

  // Handlers
  const handleNameChange = (text: string) => {
    if (!activeWorkout) return;
    setWorkoutName(text);
    setUpdatingName(true);
    // Call debounced function directly (not .call())
    debouncedUpdateName(activeWorkout.id, text);
  };

  const handleNotesChange = (text: string) => {
    if (!activeWorkout) return;
    setWorkoutNotes(text);
    setUpdatingNotes(true);
    // Call debounced function directly (not .call())
    debouncedUpdateNotes(activeWorkout.id, text);
  };

  const handleStartWorkout = async () => {
    try {
      setLoading(true);
      const workout = await workoutApi.start();
      setActiveWorkout(workout);

      // CRITICAL: Refresh status so ActiveWorkoutBar appears everywhere
      // ActiveWorkoutBar uses userStatus.active_workout, not workoutStore.activeWorkout
      const status = await userApi.getStatus();
      setUserStatus(status);
    } catch (error) {
      console.error('Error starting workout:', error);
      // TODO: Show error message to user
    } finally {
      setLoading(false);
    }
  };

  if (loading && !activeWorkoutLoaded) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  const handleSelectExercise = async (exercise: Exercise) => {
    if (!activeWorkout) return;
    
    try {
      setError(null);
      setLoading(true);
      
      // Add exercise to workout (non-optimistic: wait for API response)
      // This is safer for Day 2 - we can add optimistic updates later once set CRUD is stable
      const updatedWorkout = await workoutApi.addExercise(activeWorkout.id, {
        exercise_id: exercise.id,
      });
      
      // Update workout in store with server response
      setActiveWorkout(updatedWorkout);
      
      // Close modal
      setExercisePickerVisible(false);
    } catch (err: any) {
      console.error('Error adding exercise:', err);
      
      // Parse error message
      let errorMessage = 'Failed to add exercise';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
      // Keep modal open so user can retry
    } finally {
      setLoading(false);
    }
  };

  const refreshWorkout = async () => {
    if (!activeWorkout) return;
    
    try {
      setRefreshing(true);
      const workout = await workoutApi.getActive();
      if (workout) {
        setActiveWorkout(workout);
      }
    } catch (error) {
      console.error('Error refreshing workout:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddSet = async (exerciseId: string, data: {
    reps?: number;
    weight?: number;
    duration_seconds?: number;
    set_type: any;
    rpe?: any;
    rest_time_seconds?: number;
  }) => {
    if (!activeWorkout) return;
    
    try {
      setError(null);
      setLoading(true);
      
      // Check network - adding sets requires network (not queued)
      try {
        await workoutApi.addSet(exerciseId, data);
        
        // Clear previous performance cache (new set may affect performance data)
        userApi.clearLastPerformanceCache();
        
        // Refresh workout to get updated sets
        const workout = await workoutApi.getActive();
        if (workout) {
          setActiveWorkout(workout);
        }
        
        setAddSetFormVisible(false);
        setSelectedExerciseId(null);
      } catch (networkError: any) {
        // If network error, show message that network is required
        if (!networkError.response) {
          // Network error (no response)
          setError('Network error: Need internet connection to add new sets');
          return;
        }
        throw networkError; // Re-throw other errors
      }
    } catch (err: any) {
      console.error('Error adding set:', err);
      let errorMessage = 'Failed to add set';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSet = async (setId: string, data: {
    reps?: number;
    weight?: number;
    duration_seconds?: number;
    set_type?: any;
    rpe?: any;
    rest_time_seconds?: number;
  }) => {
    if (!activeWorkout) return;
    
    try {
      setError(null);
      setLoading(true);
      
      try {
        // Try to update online
        await workoutApi.updateSet(setId, data);
        
        // Clear previous performance cache (set edit may affect performance data)
        userApi.clearLastPerformanceCache();
        
        // Refresh workout to get updated sets
        const workout = await workoutApi.getActive();
        if (workout) {
          setActiveWorkout(workout);
        }
        
        setEditSetFormVisible(false);
        setSelectedSet(null);
      } catch (networkError: any) {
        // Check if it's a network error (no response)
        if (!networkError.response) {
          // Offline: add to queue and update UI optimistically
          await addToQueue({
            action: 'edit_set',
            set_id: setId,
            data: data,
            timestamp: Date.now(),
          });
          
          // Update UI optimistically (update local state)
          const updatedExercises = activeWorkout.exercises.map((ex) => ({
            ...ex,
            sets: ex.sets.map((set) =>
              set.id === setId ? { ...set, ...data } : set
            ),
          }));
          setActiveWorkout({ ...activeWorkout, exercises: updatedExercises });
          
          setEditSetFormVisible(false);
          setSelectedSet(null);
          
          // Show alert
          Alert.alert('Saved Locally', 'Changes saved locally. Will sync when network returns.');
          return;
        }
        // Re-throw other errors (API errors, validation errors, etc.)
        throw networkError;
      }
    } catch (err: any) {
      console.error('Error updating set:', err);
      let errorMessage = 'Failed to update set';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleMoveExerciseUp = async (exerciseIndex: number) => {
    if (!activeWorkout || exerciseIndex === 0) return;
    
    try {
      setError(null);
      setLoading(true);
      
      // Get sorted exercises
      const sortedExercises = [...activeWorkout.exercises].sort((a, b) => a.order_index - b.order_index);
      const currentExercise = sortedExercises[exerciseIndex];
      const previousExercise = sortedExercises[exerciseIndex - 1];
      
      // Create new order: swap current exercise with previous one
      const newOrder = sortedExercises.map((ex, idx) => {
        if (idx === exerciseIndex) {
          return { workout_exercise_id: ex.id, order_index: previousExercise.order_index };
        } else if (idx === exerciseIndex - 1) {
          return { workout_exercise_id: ex.id, order_index: currentExercise.order_index };
        } else {
          return { workout_exercise_id: ex.id, order_index: ex.order_index };
        }
      });
      
      // Normalize order_index to be sequential (0, 1, 2, ...)
      const normalizedOrder = newOrder
        .sort((a, b) => a.order_index - b.order_index)
        .map((item, idx) => ({
          workout_exercise_id: item.workout_exercise_id,
          order_index: idx
        }));
      
      const updatedWorkout = await workoutApi.reorderExercises(activeWorkout.id, {
        items: normalizedOrder
      });
      
      setActiveWorkout(updatedWorkout);
    } catch (err: any) {
      console.error('Error moving exercise up:', err);
      let errorMessage = 'Failed to reorder exercises';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleMoveExerciseDown = async (exerciseIndex: number) => {
    if (!activeWorkout) return;
    
    const sortedExercises = [...activeWorkout.exercises].sort((a, b) => a.order_index - b.order_index);
    if (exerciseIndex === sortedExercises.length - 1) return;
    
    try {
      setError(null);
      setLoading(true);
      
      const currentExercise = sortedExercises[exerciseIndex];
      const nextExercise = sortedExercises[exerciseIndex + 1];
      
      // Create new order: swap current exercise with next one
      const newOrder = sortedExercises.map((ex, idx) => {
        if (idx === exerciseIndex) {
          return { workout_exercise_id: ex.id, order_index: nextExercise.order_index };
        } else if (idx === exerciseIndex + 1) {
          return { workout_exercise_id: ex.id, order_index: currentExercise.order_index };
        } else {
          return { workout_exercise_id: ex.id, order_index: ex.order_index };
        }
      });
      
      // Normalize order_index to be sequential (0, 1, 2, ...)
      const normalizedOrder = newOrder
        .sort((a, b) => a.order_index - b.order_index)
        .map((item, idx) => ({
          workout_exercise_id: item.workout_exercise_id,
          order_index: idx
        }));
      
      const updatedWorkout = await workoutApi.reorderExercises(activeWorkout.id, {
        items: normalizedOrder
      });
      
      setActiveWorkout(updatedWorkout);
    } catch (err: any) {
      console.error('Error moving exercise down:', err);
      let errorMessage = 'Failed to reorder exercises';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSet = (setId: string) => {
    Alert.alert(
      'Delete Set',
      'Are you sure you want to delete this set?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            if (!activeWorkout) return;
            
            try {
              setError(null);
              setLoading(true);
              
              try {
                // Try to delete online
                await workoutApi.deleteSet(setId);
                
                // Clear previous performance cache (set deletion may affect performance data)
                userApi.clearLastPerformanceCache();
                
                // Refresh workout to get updated sets
                const workout = await workoutApi.getActive();
                if (workout) {
                  setActiveWorkout(workout);
                }
              } catch (networkError: any) {
                // Check if it's a network error (no response)
                if (!networkError.response) {
                  // Offline: add to queue and update UI optimistically
                  await addToQueue({
                    action: 'delete_set',
                    set_id: setId,
                    timestamp: Date.now(),
                  });
                  
                  // Update UI optimistically (remove from local state)
                  const updatedExercises = activeWorkout.exercises.map((ex) => ({
                    ...ex,
                    sets: ex.sets.filter((set) => set.id !== setId),
                  }));
                  setActiveWorkout({ ...activeWorkout, exercises: updatedExercises });
                  
                  // Show alert
                  Alert.alert('Saved Locally', 'Set deleted locally. Will sync when network returns.');
                  return;
                }
                // Re-throw other errors
                throw networkError;
              }
            } catch (err: any) {
              console.error('Error deleting set:', err);
              let errorMessage = 'Failed to delete set';
              if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
              }
              setError(errorMessage);
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleFinishWorkout = async (
    completionStatus: CompletionStatus,
    notes?: string
  ) => {
    if (!activeWorkout) return;

    // ⚠️ LOCKED: Finish workout requires network (do not queue)
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      Alert.alert(
        'No Internet',
        'Finish workout requires internet connection. Please connect and try again.'
      );
      return; // Do not proceed, do not queue
    }

    try {
      setFinishLoading(true);
      setError(null);
      
      await workoutApi.finishWorkout(
        activeWorkout.id,
        completionStatus,
        notes
      );

      // Clear previous performance cache (new workout may have changed performance)
      userApi.clearLastPerformanceCache();

      // Clear active workout from store
      clearActiveWorkout();

      // Refresh user status to update active workout bar
      const status = await userApi.getStatus();
      setUserStatus(status);

      // Show success message
      Alert.alert('Success', 'Workout finished successfully!');

      // Navigate to history tab
      navigation.navigate('History');

      // Close modal
      setFinishModalVisible(false);
    } catch (error: any) {
      console.error('Error finishing workout:', error);
      let errorMessage = 'Failed to finish workout. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      Alert.alert('Error', errorMessage);
    } finally {
      setFinishLoading(false);
    }
  };

  const handleDiscardWorkout = async () => {
    if (!activeWorkout) return;

    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      Alert.alert(
        'No Internet',
        'Discard workout requires internet connection. Please connect and try again.'
      );
      return;
    }

    Alert.alert(
      'Discard workout',
      'Are you sure? This workout will not be saved.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Discard',
          style: 'destructive',
          onPress: async () => {
            try {
              setDiscardLoading(true);
              setError(null);
              await workoutApi.discardWorkout(activeWorkout.id);
              userApi.clearLastPerformanceCache();
              clearActiveWorkout();
              const status = await userApi.getStatus();
              setUserStatus(status);
              setFinishModalVisible(false);
            } catch (err: unknown) {
              const msg = err && typeof (err as any).response?.data?.detail === 'string'
                ? (err as any).response.data.detail
                : 'Failed to discard workout. Please try again.';
              Alert.alert('Error', msg);
            } finally {
              setDiscardLoading(false);
            }
          },
        },
      ]
    );
  };

  if (activeWorkout) {
    const sortedExercises = [...activeWorkout.exercises].sort((a, b) => a.order_index - b.order_index);
    const actionBarPaddingBottom = Math.max(insets.bottom, 12);
    const listPaddingBottom = WORKOUT_ACTION_BAR_HEIGHT + actionBarPaddingBottom;

    // Hevy-like stats: duration, volume, sets
    const totalSets = activeWorkout.exercises.reduce((acc, ex) => acc + (ex.sets?.length ?? 0), 0);
    const totalVolumeKg = activeWorkout.exercises.reduce((acc, ex) => {
      (ex.sets ?? []).forEach((s) => {
        if (s.weight != null) acc += s.weight * (s.reps ?? 1);
      });
      return acc;
    }, 0);
    const volumeDisplay = convertWeightForDisplay(totalVolumeKg, units);
    const volumeStr = volumeDisplay != null ? `${Math.round(volumeDisplay)} ${unitLabel}` : `0 ${unitLabel}`;

    const workoutListHeader = (
      <>
        {/* Stats row - Hevy style */}
        <View style={styles.workoutStatsRow}>
          <View style={styles.workoutStat}>
            <Text style={styles.workoutStatLabel}>Duration</Text>
            <View style={styles.workoutStatValueWrap}>
              <Timer startTime={activeWorkout.start_time} />
            </View>
          </View>
          <View style={styles.workoutStat}>
            <Text style={styles.workoutStatLabel}>Volume</Text>
            <Text style={styles.workoutStatValue}>{volumeStr}</Text>
          </View>
          <View style={styles.workoutStat}>
            <Text style={styles.workoutStatLabel}>Sets</Text>
            <Text style={styles.workoutStatValue}>{totalSets}</Text>
          </View>
        </View>
        <Text style={styles.title}>Workout Session</Text>
        <View style={styles.nameContainer}>
          <TextInput
            style={styles.workoutName}
            value={workoutName}
            onChangeText={handleNameChange}
            placeholder="Workout name (optional)"
            placeholderTextColor="#999"
            editable={!loading && !finishLoading && !discardLoading}
          />
          {updatingName && (
            <ActivityIndicator size="small" color="#007AFF" style={styles.updateIndicator} />
          )}
        </View>
        <View style={styles.notesContainer}>
          {!showNotes ? (
            <TouchableOpacity style={styles.showNotesButton} onPress={() => setShowNotes(true)}>
              <Text style={styles.showNotesText}>{workoutNotes ? 'Edit notes' : 'Add notes'}</Text>
            </TouchableOpacity>
          ) : (
            <>
              <TextInput
                style={styles.notesInput}
                value={workoutNotes}
                onChangeText={handleNotesChange}
                placeholder="Add notes about your workout..."
                placeholderTextColor="#999"
                multiline
                numberOfLines={4}
                editable={!loading && !finishLoading && !discardLoading}
              />
              {updatingNotes && (
                <ActivityIndicator size="small" color="#007AFF" style={styles.updateIndicator} />
              )}
              <TouchableOpacity style={styles.hideNotesButton} onPress={() => setShowNotes(false)}>
                <Text style={styles.hideNotesText}>Hide notes</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
        {queueLength > 0 && (
          <View style={styles.queueIndicator}>
            <Text style={styles.queueIndicatorText}>
              {queueLength} {queueLength === 1 ? 'change' : 'changes'} saved locally. Syncing...
            </Text>
          </View>
        )}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity onPress={() => setError(null)}>
              <Text style={styles.dismissError}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        )}
      </>
    );

    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        {!isOnline && <OfflineBanner />}
        <GoalLabel />
        <FlatList
          data={sortedExercises}
          keyExtractor={(item) => item.id}
          ListHeaderComponent={workoutListHeader}
          contentContainerStyle={[
            styles.exerciseList,
            { paddingBottom: listPaddingBottom },
          ]}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={refreshWorkout} />
          }
          ListEmptyComponent={
            <View style={styles.emptyStateHevy}>
              <Text style={styles.emptyStateIcon}>🏋️</Text>
              <Text style={styles.emptyStateTitle}>Get started</Text>
              <Text style={styles.emptyStateSubtitle}>Add an exercise to start your workout</Text>
            </View>
          }
          renderItem={({ item, index }) => (
            <ExerciseCard
              exercise={item}
              onAddSet={() => {
                setSelectedExerciseId(item.id);
                setAddSetFormVisible(true);
              }}
              onEditSet={(set) => {
                setSelectedSet(set);
                setEditSetFormVisible(true);
              }}
              onDeleteSet={handleDeleteSet}
              onMoveUp={() => handleMoveExerciseUp(index)}
              onMoveDown={() => handleMoveExerciseDown(index)}
              canMoveUp={index > 0 && !loading}
              canMoveDown={index < sortedExercises.length - 1 && !loading}
            />
          )}
        />
        {/* Hevy-like: Add Exercise + Discard only (Finish is in header) */}
        <View style={[styles.workoutActionBar, { paddingBottom: actionBarPaddingBottom }]}>
          <TouchableOpacity
            style={[styles.actionBarAdd, (loading || !isOnline) && styles.addExerciseButtonDisabled]}
            onPress={() => setExercisePickerVisible(true)}
            disabled={loading || !isOnline}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <>
                <Text style={styles.actionBarAddIcon}>+</Text>
                <Text style={styles.actionBarAddLabel} numberOfLines={1}>Add Exercise</Text>
              </>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionBarDiscard, (loading || finishLoading || discardLoading || !isOnline) && styles.discardButtonDisabled]}
            onPress={handleDiscardWorkout}
            disabled={loading || finishLoading || discardLoading || !isOnline}
            activeOpacity={0.8}
          >
            <Text style={styles.actionBarDiscardLabel} numberOfLines={1}>{discardLoading ? '...' : 'Discard'}</Text>
          </TouchableOpacity>
        </View>

        {/* Exercise Picker Modal */}
        <ExercisePicker
          visible={exercisePickerVisible}
          onClose={() => setExercisePickerVisible(false)}
          onSelect={handleSelectExercise}
        />

        {/* Add Set Form Modal */}
        <AddSetForm
          visible={addSetFormVisible}
          onClose={() => {
            setAddSetFormVisible(false);
            setSelectedExerciseId(null);
          }}
          onSubmit={async (data) => {
            if (selectedExerciseId) {
              await handleAddSet(selectedExerciseId, data);
            }
          }}
        />

        {/* Edit Set Form Modal */}
        <EditSetForm
          visible={editSetFormVisible}
          set={selectedSet}
          onClose={() => {
            setEditSetFormVisible(false);
            setSelectedSet(null);
          }}
          onSubmit={async (setId, data) => {
            await handleUpdateSet(setId, data);
          }}
        />

        {/* Finish Workout Modal */}
        <FinishWorkoutModal
          visible={finishModalVisible}
          onClose={() => setFinishModalVisible(false)}
          onFinish={handleFinishWorkout}
          loading={finishLoading}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!isOnline && <OfflineBanner />}
      <GoalLabel />
      <StatusChipsRow metrics={metrics} />
      <TimelineSnapshotCard
        prediction={timelineLatest}
        onPress={() => (navigation.getParent() as any)?.navigate('TimelineDetails')}
      />
      {coachLoading && (
        <View style={styles.coachLoadingRow}>
          <ActivityIndicator size="small" />
          <Text style={styles.coachLoadingText}>Loading coach...</Text>
        </View>
      )}
      {coachError && (
        <View style={styles.coachErrorRow}>
          <Text style={styles.coachErrorText}>{coachError}</Text>
          <TouchableOpacity onPress={refetchCoach}>
            <Text style={styles.retryLink}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}
      <View style={styles.centerContainer}>
        <Text style={styles.emptyTitle}>Ready to start your workout?</Text>
        <TouchableOpacity
          style={[styles.startButton, (!isOnline || loading) && styles.startButtonDisabled]}
          onPress={handleStartWorkout}
          disabled={loading || !isOnline}
        >
          <Text style={styles.startButtonText}>
            {loading ? 'Starting...' : 'Start Workout'}
          </Text>
        </TouchableOpacity>
        {!isOnline && (
          <Text style={styles.offlineHint}>Go online to start a workout.</Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 16,
    paddingHorizontal: 20,
    paddingTop: 20,
    color: '#000',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  emptyTitle: {
    fontSize: 20,
    marginBottom: 30,
    color: '#333',
  },
  startButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 40,
    paddingVertical: 15,
    borderRadius: 10,
  },
  startButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  startButtonDisabled: {
    backgroundColor: '#999',
    opacity: 0.8,
  },
  offlineHint: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  workoutSessionCompact: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#f5f5f5',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e0e0e0',
  },
  workoutStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginHorizontal: 20,
    marginBottom: 8,
    backgroundColor: '#f8f8f8',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#eee',
  },
  workoutStat: {
    alignItems: 'center',
    flex: 1,
  },
  workoutStatLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
    fontWeight: '500',
  },
  workoutStatValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#007AFF',
  },
  workoutStatValueWrap: {
    minHeight: 22,
    justifyContent: 'center',
  },
  headerFinishButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 8,
  },
  headerFinishText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  headerFinishDisabled: {
    color: '#999',
    opacity: 0.7,
  },
  emptyStateHevy: {
    paddingVertical: 48,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  emptyStateIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  emptyStateSubtitle: {
    fontSize: 15,
    color: '#666',
    textAlign: 'center',
  },
  workoutActionBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: 'row',
    alignItems: 'stretch',
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 10,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e8e8e8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 8,
  },
  actionBarAdd: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 10,
    borderRadius: 10,
    gap: 4,
  },
  actionBarAddIcon: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionBarAddLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  actionBarFinish: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#34C759',
    paddingVertical: 10,
    borderRadius: 10,
  },
  actionBarFinishLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  actionBarDiscard: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#FF3B30',
    backgroundColor: 'transparent',
  },
  actionBarDiscardLabel: {
    color: '#FF3B30',
    fontSize: 13,
    fontWeight: '600',
  },
  addExerciseButtonContainer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 20,
    backgroundColor: '#fff',
  },
  addExerciseButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    shadowColor: '#007AFF',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  addExerciseButtonIcon: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '300',
    marginRight: 6,
  },
  addExerciseButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  exerciseList: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 20,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
  errorContainer: {
    backgroundColor: '#fee',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 14,
    flex: 1,
  },
  dismissError: {
    color: '#d32f2f',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 12,
  },
  queueIndicator: {
    backgroundColor: '#e3f2fd',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    marginHorizontal: 20,
    marginTop: 8,
  },
  queueIndicatorText: {
    color: '#1976d2',
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
  },
  addExerciseButtonDisabled: {
    opacity: 0.6,
  },
  finishButton: {
    backgroundColor: '#34C759',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
    shadowColor: '#34C759',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  finishButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  finishButtonDisabled: {
    opacity: 0.6,
  },
  discardButton: {
    marginTop: 10,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: 'transparent',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FF3B30',
    alignSelf: 'center',
  },
  discardButtonText: {
    color: '#FF3B30',
    fontSize: 15,
    fontWeight: '500',
  },
  discardButtonDisabled: {
    opacity: 0.5,
  },
  nameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  workoutName: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    paddingBottom: 4,
  },
  updateIndicator: {
    marginLeft: 8,
  },
  notesContainer: {
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  showNotesButton: {
    paddingVertical: 8,
  },
  showNotesText: {
    color: '#007AFF',
    fontSize: 14,
  },
  notesInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 8,
  },
  hideNotesButton: {
    alignSelf: 'flex-end',
    paddingVertical: 4,
  },
  hideNotesText: {
    color: '#666',
    fontSize: 12,
  },
  coachLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 8,
    marginHorizontal: 20,
  },
  coachLoadingText: {
    fontSize: 14,
    color: '#666',
  },
  coachErrorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 8,
    marginHorizontal: 20,
  },
  coachErrorText: {
    fontSize: 14,
    color: '#d32f2f',
  },
  retryLink: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
});
