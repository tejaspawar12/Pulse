/**
 * Timer component that displays elapsed time from server start_time.
 * 
 * LOCKED: Uses server start_time as source of truth.
 * Computes elapsed time client-side: elapsed = Date.now() - new Date(startTime).getTime()
 * 
 * Format:
 * - MM:SS for workouts < 60 minutes
 * - HH:MM:SS for workouts ≥ 60 minutes
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface TimerProps {
  startTime: string; // ISO datetime string from server (timezone-aware)
}

export const Timer: React.FC<TimerProps> = ({ startTime }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Compute elapsed time from server start_time
    const updateElapsed = () => {
      const start = new Date(startTime).getTime();
      
      // Handle invalid startTime (NaN check)
      if (Number.isNaN(start)) {
        setElapsed(0);
        return;
      }
      
      const now = Date.now();
      const elapsedMs = now - start;
      
      // Handle negative elapsed (shouldn't happen, but defensive)
      if (elapsedMs < 0) {
        setElapsed(0);
        return;
      }
      
      setElapsed(Math.floor(elapsedMs / 1000)); // Convert to seconds
    };

    // Update immediately
    updateElapsed();
    
    // Update every second
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  /**
   * Format elapsed seconds as MM:SS or HH:MM:SS.
   * LOCKED: MM:SS for < 60 min, HH:MM:SS for ≥ 60 min
   */
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      // HH:MM:SS format (≥ 60 minutes)
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      // MM:SS format (< 60 minutes)
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.timeText}>{formatTime(elapsed)}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    fontFamily: 'monospace', // Monospace for consistent width
  },
});
