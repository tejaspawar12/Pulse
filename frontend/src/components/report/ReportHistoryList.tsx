/**
 * ReportHistoryList: list of past weekly reports (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';

interface ReportHistoryListProps {
  reports: WeeklyReport[];
  onSelectReport?: (report: WeeklyReport) => void;
}

function formatWeekLabel(weekStart: string): string {
  const d = new Date(weekStart);
  const end = new Date(d);
  end.setDate(end.getDate() + 6);
  return `${d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })} – ${end.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })}`;
}

export const ReportHistoryList: React.FC<ReportHistoryListProps> = ({
  reports,
  onSelectReport,
}) => {
  if (!reports.length) return null;
  return (
    <View style={styles.section}>
      <Text style={styles.title}>Past reports</Text>
      <FlatList
        data={reports}
        keyExtractor={(item) => item.id}
        scrollEnabled={false}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.row}
            onPress={() => onSelectReport?.(item)}
            disabled={!onSelectReport}
          >
            <Text style={styles.weekLabel}>{formatWeekLabel(item.week_start)}</Text>
            <Text style={styles.meta}>
              {item.workouts_count ?? 0} workouts
              {item.status === 'insufficient_data' ? ' · Insufficient data' : ''}
            </Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    marginTop: 8,
    marginBottom: 24,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111',
  },
  row: {
    paddingVertical: 12,
    paddingHorizontal: 0,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  weekLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111',
  },
  meta: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
});
