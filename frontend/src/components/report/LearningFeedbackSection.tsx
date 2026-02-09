/**
 * LearningFeedbackSection: positive signal (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';

interface LearningFeedbackSectionProps {
  report: WeeklyReport | null;
}

export const LearningFeedbackSection: React.FC<LearningFeedbackSectionProps> = ({
  report,
}) => {
  if (!report?.positive_signal_label) return null;
  return (
    <View style={styles.section}>
      <Text style={styles.title}>What went well</Text>
      <Text style={styles.label}>{report.positive_signal_label}</Text>
      {report.positive_signal_reason ? (
        <Text style={styles.reason}>{report.positive_signal_reason}</Text>
      ) : null}
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
  reason: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
