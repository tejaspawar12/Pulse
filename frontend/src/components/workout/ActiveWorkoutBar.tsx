/**
 * Active Workout Bar component.
 * 
 * LOCKED: Appears on all tabs when workout is active.
 * Cannot be dismissed while workout is active.
 * Shows "Workout in progress", elapsed time, and "Resume" button.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Timer } from '../common/Timer';

interface ActiveWorkoutBarProps {
  startTime: string; // ISO datetime string from server
}

export const ActiveWorkoutBar: React.FC<ActiveWorkoutBarProps> = ({
  startTime,
}) => {
  const navigation = useNavigation<any>(); // Use any for now, typed navigation in production
  const insets = useSafeAreaInsets();

  const handleResume = () => {
    // Navigate to Log tab (workout session screen)
    navigation.navigate('Log');
  };

  return (
    <View style={[styles.container, { paddingBottom: Math.max(insets.bottom, 6) }]}>
      <Text style={styles.label}>Workout in progress</Text>
      <View style={styles.timerContainer}>
        <Timer startTime={startTime} />
      </View>
      <TouchableOpacity onPress={handleResume} style={styles.button}>
        <Text style={styles.buttonText}>Resume</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    paddingBottom: 6, // Reduced bottom padding to avoid covering tab bar
    backgroundColor: '#f0f0f0',
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    // Note: Current approach renders below Tab.Navigator (OK for Day 5)
    // Future improvement: Use position: 'absolute' with bottom: 0 for floating footer feel
    // If using absolute positioning, must add padding to screens to prevent content overlap
  },
  label: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  timerContainer: {
    flex: 1,
    alignItems: 'center',
  },
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    flex: 1,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
});
