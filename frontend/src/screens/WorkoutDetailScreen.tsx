/**
 * Workout Detail Screen - Displays full workout details.
 * Phase 2 Week 4: When offline show cached detail if available; when online fetch and cache.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  ScrollView,
  Text,
  ActivityIndicator,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { WorkoutOut, CompletionStatus } from '../types/workout.types';
import { workoutApi } from '../services/api/workout.api';
import { ExerciseDetailCard } from '../components/workout/ExerciseDetailCard';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { OfflineBanner } from '../components/common/OfflineBanner';

type WorkoutDetailRouteParams = {
  workoutId: string;
};

type WorkoutDetailRouteProp = RouteProp<{ WorkoutDetail: WorkoutDetailRouteParams }, 'WorkoutDetail'>;

export const WorkoutDetailScreen: React.FC = () => {
  const route = useRoute<WorkoutDetailRouteProp>();
  const navigation = useNavigation<any>();
  const { workoutId } = route.params;

  const { isOnline, cachedWorkoutDetails, getCachedOrFetchWorkoutDetail } = useOfflineCache();

  const [workout, setWorkout] = useState<WorkoutOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const loadWorkout = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCachedOrFetchWorkoutDetail(workoutId, () =>
        workoutApi.getWorkoutDetail(workoutId)
      );
      setWorkout(data ?? null);
      if (!data && !isOnline) {
        setError('This workout isn\'t in cache. Go online and open it once to view offline.');
      } else if (!data) {
        setError('Failed to load workout details');
      }
    } catch (err: any) {
      console.error('Error loading workout detail:', err);
      const cached = cachedWorkoutDetails[workoutId];
      if (!isOnline && cached) {
        setWorkout(cached);
      } else {
        setError(err.response?.data?.detail || 'Failed to load workout details');
      }
    } finally {
      setLoading(false);
    }
  }, [workoutId, isOnline, cachedWorkoutDetails, getCachedOrFetchWorkoutDetail]);

  const loadAiSummary = useCallback(async () => {
    if (!isOnline) {
      setSummaryError('Offline. Connect to get an AI summary.');
      return;
    }
    setLoadingSummary(true);
    setSummaryError(null);
    try {
      const { summary } = await workoutApi.getWorkoutAISummary(workoutId);
      setAiSummary(summary || null);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to generate summary';
      setSummaryError(typeof msg === 'string' ? msg : 'Failed to generate summary');
    } finally {
      setLoadingSummary(false);
    }
  }, [workoutId, isOnline]);

  useEffect(() => {
    loadWorkout();
  }, [workoutId, loadWorkout]);
  
  // Format date and time from ISO datetime string
  // ⚠️ CRITICAL: ISO datetime strings are timezone-aware, parse correctly
  const formatDateTime = (isoString: string): { date: string; time: string } => {
    // Parse ISO datetime string (handles timezone correctly)
    const date = new Date(isoString);
    
    // Format date (e.g., "Jan 29, 2026")
    const dateStr = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
    
    // Format time (e.g., "2:30 PM")
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
    
    return { date: dateStr, time: timeStr };
  };
  
  // Format duration
  const formatDuration = (minutes?: number): string => {
    if (!minutes) return '—';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };
  
  // Format completion status
  const formatStatus = (status?: CompletionStatus): string => {
    if (!status) return '—';
    return status === CompletionStatus.COMPLETED ? 'Completed' : 'Partial';
  };
  
  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading workout details...</Text>
      </View>
    );
  }
  
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={loadWorkout}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  if (!workout) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Workout not found</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  const startDateTime = formatDateTime(workout.start_time);
  const endDateTime = workout.end_time ? formatDateTime(workout.end_time) : null;
  
  // Sort exercises by order_index (ascending)
  const sortedExercises = [...(workout.exercises || [])].sort(
    (a, b) => a.order_index - b.order_index
  );
  
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {!isOnline && <OfflineBanner />}
      {/* Header Section */}
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <Text style={styles.date}>{startDateTime.date}</Text>
          {workout.completion_status && (
            <View
              style={[
                styles.statusBadge,
                workout.completion_status === CompletionStatus.COMPLETED
                  ? styles.statusCompleted
                  : styles.statusPartial
              ]}
            >
              <Text
                style={[
                  styles.statusText,
                  workout.completion_status === CompletionStatus.COMPLETED
                    ? styles.statusTextCompleted
                    : styles.statusTextPartial
                ]}
              >
                {formatStatus(workout.completion_status)}
              </Text>
            </View>
          )}
        </View>
        
        <View style={styles.metadataRow}>
          <View style={styles.metadataItem}>
            <Text style={styles.metadataLabel}>Start Time</Text>
            <Text style={styles.metadataValue}>{startDateTime.time}</Text>
          </View>
          {endDateTime && (
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>End Time</Text>
              <Text style={styles.metadataValue}>{endDateTime.time}</Text>
            </View>
          )}
          <View style={styles.metadataItem}>
            <Text style={styles.metadataLabel}>Duration</Text>
            <Text style={styles.metadataValue}>{formatDuration(workout.duration_minutes)}</Text>
          </View>
        </View>
      </View>
      
      {/* Workout Name */}
      {workout.name && (
        <View style={styles.nameSection}>
          <Text style={styles.name}>{workout.name}</Text>
        </View>
      )}
      
      {/* Workout Notes */}
      {workout.notes && (
        <View style={styles.notesSection}>
          <Text style={styles.notesLabel}>Notes</Text>
          <Text style={styles.notesText}>{workout.notes}</Text>
        </View>
      )}
      
      {/* Exercises Section */}
      <View style={styles.exercisesSection}>
        <Text style={styles.sectionTitle}>Exercises</Text>
        {sortedExercises.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No exercises in this workout</Text>
          </View>
        ) : (
          sortedExercises.map((exercise) => (
            <ExerciseDetailCard
              key={exercise.id}
              exercise={exercise}
            />
          ))
        )}
      </View>

      {/* AI Summary (AI Summaries & Trends) */}
      <View style={styles.aiSummarySection}>
        <Text style={styles.sectionTitle}>AI Summary</Text>
        <Text style={styles.aiSummaryHint}>
          Get a short AI summary of this workout. Powered by your workout data only.
        </Text>
        <TouchableOpacity
          style={[styles.generateSummaryBtn, loadingSummary && styles.generateSummaryBtnDisabled]}
          onPress={loadAiSummary}
          disabled={loadingSummary || !isOnline}
        >
          {loadingSummary ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.generateSummaryBtnText}>Generate summary</Text>
          )}
        </TouchableOpacity>
        {summaryError ? (
          <Text style={styles.summaryErrorText}>{summaryError}</Text>
        ) : aiSummary ? (
          <View style={styles.summaryCard}>
            <Text style={styles.summaryText}>{aiSummary}</Text>
            <Text style={styles.poweredByLabel}>Powered by AI</Text>
          </View>
        ) : null}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 16,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    backgroundColor: '#666',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  date: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusCompleted: {
    backgroundColor: '#E8F5E9',
  },
  statusPartial: {
    backgroundColor: '#FFF3E0',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  statusTextCompleted: {
    color: '#2E7D32',
  },
  statusTextPartial: {
    color: '#E65100',
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  metadataItem: {
    alignItems: 'center',
  },
  metadataLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metadataValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  nameSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  name: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  notesSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  notesLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    fontWeight: '600',
  },
  notesText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  exercisesSection: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  emptyState: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#666',
  },
  aiSummarySection: {
    marginTop: 24,
    marginBottom: 24,
  },
  aiSummaryHint: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
  },
  generateSummaryBtn: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignSelf: 'flex-start',
  },
  generateSummaryBtnDisabled: {
    opacity: 0.6,
  },
  generateSummaryBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  summaryErrorText: {
    fontSize: 14,
    color: '#c00',
    marginTop: 10,
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  summaryText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#333',
  },
  poweredByLabel: {
    fontSize: 11,
    color: '#999',
    marginTop: 10,
  },
});
