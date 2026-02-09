/**
 * WeekSummaryCard: aggregates for a weekly report (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';
import { convertWeightForDisplay, getUnitLabel } from '../../utils/units';
import { useUserUnit } from '../../hooks/useUserUnit';

interface WeekSummaryCardProps {
  report: WeeklyReport | null;
}

export const WeekSummaryCard: React.FC<WeekSummaryCardProps> = ({ report }) => {
  const units = useUserUnit();
  const unitLabel = getUnitLabel(units);

  if (!report) return null;

  const volumeDisplay = convertWeightForDisplay(report.total_volume_kg ?? 0, units);
  const volumeStr =
    volumeDisplay != null ? `${volumeDisplay.toFixed(0)} ${unitLabel}` : '—';
  const deltaStr =
    report.volume_delta_pct != null
      ? `${report.volume_delta_pct > 0 ? '+' : ''}${report.volume_delta_pct.toFixed(0)}%`
      : '—';
  const avgDur =
    report.avg_session_duration != null
      ? `${Math.round(report.avg_session_duration)} min`
      : '—';

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Week summary</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Workouts</Text>
        <Text style={styles.value}>{report.workouts_count ?? 0}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Volume</Text>
        <Text style={styles.value}>{volumeStr}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Volume vs last week</Text>
        <Text style={styles.value}>{deltaStr}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Avg session</Text>
        <Text style={styles.value}>{avgDur}</Text>
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
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: { fontSize: 14, color: '#666' },
  value: { fontSize: 14, fontWeight: '500', color: '#111' },
});
