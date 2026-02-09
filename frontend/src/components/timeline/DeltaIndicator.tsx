/**
 * DeltaIndicator: weeks_delta and delta_reason (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { TransformationPrediction } from '../../services/api/predictions.api';

interface DeltaIndicatorProps {
  prediction: TransformationPrediction | null;
}

export const DeltaIndicator: React.FC<DeltaIndicatorProps> = ({ prediction }) => {
  if (!prediction || prediction.weeks_delta == null) return null;
  const delta = prediction.weeks_delta;
  const reason = prediction.delta_reason ?? '';
  const deltaStr =
    delta > 0 ? `+${delta} weeks` : delta < 0 ? `${delta} weeks` : 'No change';
  const color = delta < 0 ? '#28a745' : delta > 0 ? '#dc3545' : '#666';
  return (
    <View style={styles.container}>
      <Text style={[styles.delta, { color }]}>{deltaStr}</Text>
      {reason ? <Text style={styles.reason}>{reason}</Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  delta: {
    fontSize: 16,
    fontWeight: '600',
  },
  reason: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
