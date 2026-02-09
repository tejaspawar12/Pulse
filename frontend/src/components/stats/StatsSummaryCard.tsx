/**
 * Stats summary card: period_days, workouts, volume, sets, PRs, avg duration, most-trained muscle.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { StatsSummary } from '../../services/api/stats.api';
import { convertWeightForDisplay, getUnitLabel } from '../../utils/units';

interface StatsSummaryCardProps {
  summary: StatsSummary | null;
  units: 'kg' | 'lb';
}

export const StatsSummaryCard: React.FC<StatsSummaryCardProps> = ({ summary, units }) => {
  const unitLabel = getUnitLabel(units);

  if (!summary) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Summary</Text>
        <Text style={styles.empty}>No data for this period</Text>
      </View>
    );
  }

  const volumeDisplay = convertWeightForDisplay(summary.total_volume_kg, units);
  const volumeStr = volumeDisplay != null ? `${volumeDisplay.toFixed(0)} ${unitLabel}` : '—';

  const avgDuration =
    summary.avg_workout_duration_minutes != null
      ? `${Math.round(summary.avg_workout_duration_minutes)} min`
      : '—';

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Summary</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Period</Text>
        <Text style={styles.value}>{summary.period_days} days</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Workouts</Text>
        <Text style={styles.value}>{summary.total_workouts}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Volume</Text>
        <Text style={styles.value}>{volumeStr}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Sets</Text>
        <Text style={styles.value}>{summary.total_sets}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>PRs</Text>
        <Text style={styles.value}>{summary.prs_hit}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Avg duration</Text>
        <Text style={styles.value}>{avgDuration}</Text>
      </View>
      {summary.most_trained_muscle != null && (
        <View style={styles.row}>
          <Text style={styles.label}>Most trained</Text>
          <Text style={styles.value}>{summary.most_trained_muscle}</Text>
        </View>
      )}
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
  empty: {
    fontSize: 14,
    color: '#666',
  },
});
