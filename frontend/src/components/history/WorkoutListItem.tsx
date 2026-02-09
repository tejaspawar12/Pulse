/**
 * Workout List Item Component
 * Displays workout summary in history list
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { WorkoutSummary, CompletionStatus } from '../../types/workout.types';
import { parseLocalYMD, formatFullDate, isToday, isYesterday } from '../../utils/date';

interface WorkoutListItemProps {
  workout: WorkoutSummary;
  onPress: () => void;
}

export const WorkoutListItem: React.FC<WorkoutListItemProps> = ({
  workout,
  onPress
}) => {
  // Format date (YYYY-MM-DD to readable format)
  // Uses date utility for consistency and to prevent timezone shift bugs
  const formatDate = (dateStr: string): string => {
    const date = parseLocalYMD(dateStr);
    
    if (isToday(date)) {
      return 'Today';
    }
    if (isYesterday(date)) {
      return 'Yesterday';
    }
    return formatFullDate(date);
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
  const formatStatus = (status: CompletionStatus): string => {
    return status === CompletionStatus.COMPLETED ? 'Completed' : 'Partial';
  };
  
  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.date}>{formatDate(workout.date)}</Text>
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
        </View>
        
        {workout.name && (
          <Text style={styles.name} numberOfLines={1}>
            {workout.name}
          </Text>
        )}
        
        <View style={styles.stats}>
          <Text style={styles.statText}>
            {workout.exercise_count} {workout.exercise_count === 1 ? 'exercise' : 'exercises'}
          </Text>
          <Text style={styles.statSeparator}>•</Text>
          <Text style={styles.statText}>
            {workout.set_count} {workout.set_count === 1 ? 'set' : 'sets'}
          </Text>
          {workout.duration_minutes != null && workout.duration_minutes > 0 ? (
            <>
              <Text style={styles.statSeparator}>•</Text>
              <Text style={styles.statText}>{formatDuration(workout.duration_minutes)}</Text>
            </>
          ) : null}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  date: {
    fontSize: 16,
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
  name: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
    marginBottom: 8,
  },
  stats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  statText: {
    fontSize: 13,
    color: '#999',
  },
  statSeparator: {
    fontSize: 13,
    color: '#ccc',
    marginHorizontal: 8,
  },
});
