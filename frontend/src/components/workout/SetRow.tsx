/**
 * Set Row Component
 * Displays a single set in table row format.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { WorkoutSet, SetType, RPE } from '../../types/workout.types';
import { useUserUnit } from '../../hooks/useUserUnit';
import { convertWeightForDisplay, getUnitLabel } from '../../utils/units';

interface SetRowProps {
  set: WorkoutSet;
}

export const SetRow: React.FC<SetRowProps> = ({ set }) => {
  // ✅ Use selector hook instead of manual fallback
  const userUnit = useUserUnit();
  const unitLabel = getUnitLabel(userUnit);
  
  // Format set type
  const formatSetType = (type: SetType): string => {
    const typeMap: Record<SetType, string> = {
      [SetType.WORKING]: 'Working',
      [SetType.WARMUP]: 'Warm-up',
      [SetType.FAILURE]: 'Failure',
      [SetType.DROP]: 'Drop',
      [SetType.AMRAP]: 'AMRAP',
    };
    return typeMap[type] || type;
  };
  
  // Format RPE
  const formatRPE = (rpe?: RPE): string => {
    if (!rpe) return '—';
    const rpeMap: Record<RPE, string> = {
      [RPE.EASY]: 'Easy',
      [RPE.MEDIUM]: 'Medium',
      [RPE.HARD]: 'Hard',
    };
    return rpeMap[rpe] || rpe;
  };
  
  // Format weight (with user's preferred unit)
  const formatWeight = (weight?: number): string => {
    if (!weight) return '—';
    const displayWeight = convertWeightForDisplay(weight, userUnit);
    return `${displayWeight} ${unitLabel}`;
  };
  
  // Format reps
  const formatReps = (reps?: number): string => {
    if (!reps) return '—';
    return String(reps);
  };
  
  // Format duration (for time-based exercises)
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '—';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
  };
  
  return (
    <View style={styles.row}>
      <Text style={[styles.cell, styles.setNumberCell]}>
        {set.set_number}
      </Text>
      <Text style={[styles.cell, styles.repsCell]}>
        {formatReps(set.reps)}
      </Text>
      <Text style={[styles.cell, styles.weightCell]}>
        {formatWeight(set.weight)}
      </Text>
      <Text style={[styles.cell, styles.typeCell]}>
        {formatSetType(set.set_type)}
      </Text>
      <Text style={[styles.cell, styles.rpeCell]}>
        {formatRPE(set.rpe)}
      </Text>
      {/* ⚠️ NOTE: Duration can be added later: {formatDuration(set.duration_seconds)} */}
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  cell: {
    fontSize: 13,
    color: '#333',
  },
  setNumberCell: {
    width: 40,
    fontWeight: '600',
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
});
