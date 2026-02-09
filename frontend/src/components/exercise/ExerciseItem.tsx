/**
 * Exercise Item component.
 * Displays exercise name, muscle group, and equipment.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Exercise } from '../../types/exercise.types';

interface ExerciseItemProps {
  exercise: Exercise;
  onPress: (exercise: Exercise) => void;
}

export const ExerciseItem: React.FC<ExerciseItemProps> = ({ exercise, onPress }) => {
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(exercise)}
      activeOpacity={0.7}
    >
      <View style={styles.content}>
        <Text style={styles.name}>{exercise.name}</Text>
        <View style={styles.meta}>
          <Text style={styles.metaText}>{exercise.primary_muscle_group}</Text>
          <Text style={styles.separator}>•</Text>
          <Text style={styles.metaText}>{exercise.equipment}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaText: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
  },
  separator: {
    marginHorizontal: 8,
    color: '#999',
  },
});
