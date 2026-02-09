/**
 * Streak card: current streak, longest streak, last workout date.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { parseLocalYMD, formatFullDate } from '../../utils/date';

interface StreakCardProps {
  current: number;
  longest: number;
  lastWorkoutDate: string | null;
}

function formatLastWorkout(ymd: string | null): string {
  if (ymd == null) return 'Never';
  const date = parseLocalYMD(ymd);
  return formatFullDate(date);
}

export const StreakCard: React.FC<StreakCardProps> = ({
  current,
  longest,
  lastWorkoutDate,
}) => {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Streak</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Current streak</Text>
        <Text style={styles.value}>{current} days</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Longest streak</Text>
        <Text style={styles.value}>{longest} days</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Last workout</Text>
        <Text style={styles.value}>{formatLastWorkout(lastWorkoutDate)}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  label: {
    fontSize: 14,
    color: '#666',
  },
  value: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
});
