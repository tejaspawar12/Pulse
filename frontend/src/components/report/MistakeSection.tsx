/**
 * MistakeSection: primary training mistake (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';

interface MistakeSectionProps {
  report: WeeklyReport | null;
}

export const MistakeSection: React.FC<MistakeSectionProps> = ({ report }) => {
  if (!report?.primary_training_mistake_label) return null;
  return (
    <View style={styles.section}>
      <Text style={styles.title}>Primary focus area</Text>
      <Text style={styles.label}>{report.primary_training_mistake_label}</Text>
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
