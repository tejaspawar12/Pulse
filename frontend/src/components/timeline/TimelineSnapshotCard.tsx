/**
 * TimelineSnapshotCard: compact card for Log tab (Phase 2 Week 6).
 * strength_gain_weeks, visible_change_weeks, delta; onPress → TimelineDetailsScreen.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import type { TransformationPrediction } from '../../services/api/predictions.api';

interface TimelineSnapshotCardProps {
  prediction: TransformationPrediction | null;
  onPress: () => void;
}

export const TimelineSnapshotCard: React.FC<TimelineSnapshotCardProps> = ({
  prediction,
  onPress,
}) => {
  if (!prediction) return null;
  const strength = prediction.strength_gain_weeks ?? '—';
  const visible = prediction.visible_change_weeks ?? '—';
  const delta = prediction.weeks_delta;
  const deltaStr =
    delta != null
      ? delta > 0
        ? `+${delta} wk`
        : delta < 0
          ? `${delta} wk`
          : '—'
      : '—';
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <Text style={styles.title}>Transformation timeline</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Strength gains</Text>
        <Text style={styles.value}>{strength} weeks</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Visible change</Text>
        <Text style={styles.value}>{visible} weeks</Text>
      </View>
      {delta != null ? (
        <View style={styles.row}>
          <Text style={styles.label}>Vs last prediction</Text>
          <Text style={styles.value}>{deltaStr}</Text>
        </View>
      ) : null}
      <Text style={styles.tap}>Tap for details</Text>
    </TouchableOpacity>
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
    marginBottom: 10,
    color: '#111',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  label: { fontSize: 14, color: '#666' },
  value: { fontSize: 14, fontWeight: '500', color: '#111' },
  tap: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 8,
  },
});
