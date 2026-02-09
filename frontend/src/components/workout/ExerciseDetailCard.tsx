/**
 * Exercise Detail Card Component
 * Displays exercise with all sets in a table format.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { WorkoutExercise } from '../../types/workout.types';
import { SetRow } from './SetRow';

interface ExerciseDetailCardProps {
  exercise: WorkoutExercise;
}

export const ExerciseDetailCard: React.FC<ExerciseDetailCardProps> = ({
  exercise
}) => {
  // Sort sets by set_number (ascending)
  const sortedSets = [...(exercise.sets || [])].sort(
    (a, b) => a.set_number - b.set_number
  );
  
  return (
    <View style={styles.container}>
      {/* Exercise Header */}
      <View style={styles.header}>
        <Text style={styles.exerciseName}>{exercise.exercise_name}</Text>
        {exercise.notes && (
          <Text style={styles.exerciseNotes}>{exercise.notes}</Text>
        )}
      </View>
      
      {/* Sets Table */}
      {sortedSets.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No sets logged</Text>
        </View>
      ) : (
        <View style={styles.setsContainer}>
          {/* Table Header */}
          <View style={styles.tableHeader}>
            <Text style={[styles.headerCell, styles.setNumberCell]}>Set</Text>
            <Text style={[styles.headerCell, styles.repsCell]}>Reps</Text>
            <Text style={[styles.headerCell, styles.weightCell]}>Weight</Text>
            <Text style={[styles.headerCell, styles.typeCell]}>Type</Text>
            <Text style={[styles.headerCell, styles.rpeCell]}>RPE</Text>
            {/* ⚠️ NOTE: Duration column can be added later for time-based exercises */}
          </View>
          
          {/* Sets Rows */}
          {sortedSets.map((set) => (
            <SetRow key={set.id} set={set} />
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
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
  header: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  exerciseName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  exerciseNotes: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
  },
  setsContainer: {
    marginTop: 8,
  },
  tableHeader: {
    flexDirection: 'row',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    marginBottom: 8,
  },
  headerCell: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  setNumberCell: {
    width: 40,
  },
  repsCell: {
    width: 50,
  },
  weightCell: {
    width: 70,
  },
  typeCell: {
    width: 80,
    flex: 1,
  },
  rpeCell: {
    width: 50,
  },
  emptyState: {
    padding: 16,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 13,
    color: '#999',
  },
});
