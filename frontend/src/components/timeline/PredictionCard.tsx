/**
 * PredictionCard: goal-based timeline — strength/visible weeks + next milestone (Phase 2 Week 6).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { TransformationPrediction } from '../../services/api/predictions.api';

function goalToLabel(goal: string | null | undefined): string {
  if (!goal) return '';
  const g = goal.toLowerCase();
  if (g === 'strength') return 'Strength';
  if (g === 'muscle') return 'Muscle gain';
  if (g === 'weight_loss') return 'Weight loss';
  if (g === 'general') return 'General fitness';
  return goal;
}

interface PredictionCardProps {
  prediction: TransformationPrediction | null;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ prediction }) => {
  if (!prediction) return null;
  const strength = prediction.strength_gain_weeks ?? '—';
  const visible = prediction.visible_change_weeks ?? '—';
  const milestone = prediction.next_milestone ?? '—';
  const milestoneWeeks = prediction.next_milestone_weeks ?? '—';
  const goalLabel = goalToLabel(prediction.primary_goal);
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Your timeline</Text>
      {goalLabel ? (
        <Text style={styles.goalTag}>For: {goalLabel}</Text>
      ) : null}
      <View style={styles.row}>
        <Text style={styles.label}>Noticeable strength</Text>
        <Text style={styles.value}>
          {typeof strength === 'number' ? `${strength} weeks` : strength}
        </Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Visible body change</Text>
        <Text style={styles.value}>
          {typeof visible === 'number' ? `${visible} weeks` : visible}
        </Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Next milestone</Text>
        <Text style={styles.value}>
          {milestone}
          {typeof milestoneWeeks === 'number' ? ` (${milestoneWeeks} wk)` : ''}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
    color: '#111',
  },
  goalTag: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: { fontSize: 14, color: '#666' },
  value: { fontSize: 14, fontWeight: '500', color: '#111' },
});
