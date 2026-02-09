/**
 * PlanSummaryCard: display plan fields in a readable card (Phase 2 Week 7).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { Plan } from '../../services/api/plan.api';

interface PlanSummaryCardProps {
  plan: Plan | null;
}

const formatSplit = (s: string | null): string => {
  if (!s) return '—';
  return s
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
};

const formatProgression = (p: string | null): string => {
  if (!p) return '—';
  return p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
};

export const PlanSummaryCard: React.FC<PlanSummaryCardProps> = ({ plan }) => {
  if (!plan) return null;

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Your plan</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Days per week</Text>
        <Text style={styles.value}>{plan.days_per_week ?? '—'}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Session target (min)</Text>
        <Text style={styles.value}>{plan.session_duration_target ?? '—'}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Split</Text>
        <Text style={styles.value}>{formatSplit(plan.split_type)}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Volume multiplier</Text>
        <Text style={styles.value}>{plan.volume_multiplier.toFixed(1)}</Text>
      </View>
      <Text style={styles.hint}>
        Scales suggested training volume (1.0 = your baseline). Auto-adjust may change this weekly.
      </Text>
      <View style={styles.row}>
        <Text style={styles.label}>Progression</Text>
        <Text style={styles.value}>{formatProgression(plan.progression_type)}</Text>
      </View>
      {plan.deload_week_frequency != null && (
        <>
          <View style={styles.row}>
            <Text style={styles.label}>Deload every (weeks)</Text>
            <Text style={styles.value}>{plan.deload_week_frequency}</Text>
          </View>
          <Text style={styles.hint}>
            Every {plan.deload_week_frequency} week(s) the plan can apply a lighter week to support recovery.
          </Text>
        </>
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
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#111',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#eee',
  },
  label: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  value: {
    fontSize: 14,
    color: '#333',
    fontWeight: '400',
  },
  hint: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    marginBottom: 8,
    fontStyle: 'italic',
  },
});
