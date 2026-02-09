/**
 * AdjustmentMetricSnapshot: "Why this change?" — metrics_snapshot (Phase 2 Week 7).
 * Displays consistency_score, burnout_risk, momentum_trend from adjustment.metrics_snapshot.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { MetricsSnapshot } from '../../services/api/plan.api';

interface AdjustmentMetricSnapshotProps {
  metrics: MetricsSnapshot | null;
}

const formatRisk = (s: string | undefined): string => {
  if (!s) return '—';
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
};

const formatMomentum = (s: string | undefined): string => {
  if (!s) return '—';
  const lower = s.toLowerCase();
  if (lower === 'rising') return 'Rising';
  if (lower === 'falling') return 'Falling';
  if (lower === 'stable') return 'Stable';
  return s;
};

export const AdjustmentMetricSnapshot: React.FC<AdjustmentMetricSnapshotProps> = ({
  metrics,
}) => {
  if (!metrics) return null;

  const score =
    metrics.consistency_score != null
      ? Math.round(metrics.consistency_score).toString()
      : '—';
  const risk = formatRisk(metrics.burnout_risk);
  const momentum = formatMomentum(metrics.momentum_trend);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Why this change?</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Consistency</Text>
        <Text style={styles.value}>{score}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Burnout risk</Text>
        <Text style={styles.value}>{risk}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Momentum</Text>
        <Text style={styles.value}>{momentum}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#555',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  label: {
    fontSize: 13,
    color: '#666',
  },
  value: {
    fontSize: 13,
    color: '#333',
    fontWeight: '500',
  },
});
