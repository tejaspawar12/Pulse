/**
 * FocusSection: weekly focus (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';

interface FocusSectionProps {
  report: WeeklyReport | null;
}

export const FocusSection: React.FC<FocusSectionProps> = ({ report }) => {
  if (!report?.weekly_focus_label) return null;
  return (
    <View style={styles.section}>
      <Text style={styles.title}>This week's focus</Text>
      <Text style={styles.label}>{report.weekly_focus_label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    marginBottom: 16,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  label: {
    fontSize: 16,
    color: '#111',
  },
});
