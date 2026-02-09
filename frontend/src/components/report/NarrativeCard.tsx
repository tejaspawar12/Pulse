/**
 * NarrativeCard: LLM or fallback narrative (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { WeeklyReport } from '../../services/api/reports.api';

interface NarrativeCardProps {
  report: WeeklyReport | null;
}

export const NarrativeCard: React.FC<NarrativeCardProps> = ({ report }) => {
  if (!report?.narrative) return null;
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Summary</Text>
      <Text style={styles.narrative}>{report.narrative}</Text>
      {report.narrative_source ? (
        <Text style={styles.source}>
          {report.narrative_source === 'llm' ? 'AI summary' : 'Summary'}
        </Text>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#111',
  },
  narrative: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  source: {
    fontSize: 12,
    color: '#888',
    marginTop: 8,
  },
});
