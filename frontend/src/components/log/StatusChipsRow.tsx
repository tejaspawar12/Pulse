/**
 * StatusChipsRow: momentum and risk chips; "Why?" opens WhyDrawer (Phase 2 Week 5 Day 5).
 */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import type { MetricsState } from '../../hooks/useCoach';
import { WhyDrawer } from './WhyDrawer';

interface StatusChipsRowProps {
  metrics: MetricsState;
}

export const StatusChipsRow: React.FC<StatusChipsRowProps> = ({ metrics }) => {
  const [whyVisible, setWhyVisible] = useState(false);
  const hasReasons = metrics.reasons && metrics.reasons.length > 0;

  return (
    <View style={styles.row}>
      {metrics.momentumTrend ? (
        <View style={[styles.chip, styles.chipNeutral]}>
          <Text style={styles.chipLabel}>Momentum</Text>
          <Text style={styles.chipValue}>{metrics.momentumTrend}</Text>
        </View>
      ) : null}
      {metrics.dropoutRisk ? (
        <View style={[styles.chip, metrics.dropoutRisk === 'high' ? styles.chipRisk : styles.chipNeutral]}>
          <Text style={styles.chipLabel}>Dropout risk</Text>
          <Text style={styles.chipValue}>{metrics.dropoutRisk}</Text>
        </View>
      ) : null}
      {metrics.consistencyScore != null ? (
        <View style={styles.chip}>
          <Text style={styles.chipLabel}>Consistency</Text>
          <Text style={styles.chipValue}>{Math.round(metrics.consistencyScore)}%</Text>
        </View>
      ) : null}
      {hasReasons && (
        <TouchableOpacity style={styles.whyButton} onPress={() => setWhyVisible(true)}>
          <Text style={styles.whyButtonText}>Why?</Text>
        </TouchableOpacity>
      )}
      <WhyDrawer
        visible={whyVisible}
        onClose={() => setWhyVisible(false)}
        reasons={metrics.reasons ?? []}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  chip: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#e8f5e9',
  },
  chipNeutral: {
    backgroundColor: '#f5f5f5',
  },
  chipRisk: {
    backgroundColor: '#ffebee',
  },
  chipLabel: {
    fontSize: 10,
    color: '#666',
    textTransform: 'uppercase',
  },
  chipValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
  },
  whyButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#e3f2fd',
  },
  whyButtonText: {
    fontSize: 13,
    color: '#1976d2',
    fontWeight: '600',
  },
});
