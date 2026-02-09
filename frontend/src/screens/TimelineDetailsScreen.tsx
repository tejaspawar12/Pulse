/**
 * TimelineDetailsScreen: transformation timeline prediction + history (Phase 2 Week 6).
 * Available to all authenticated users.
 */
import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useTransformationPredictions } from '../hooks/useTransformationPredictions';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { PredictionCard } from '../components/timeline/PredictionCard';
import { DeltaIndicator } from '../components/timeline/DeltaIndicator';
import type { TransformationPrediction } from '../services/api/predictions.api';

function formatGoalLabel(goal: string | null | undefined): string {
  if (!goal) return '';
  const g = goal.toLowerCase();
  if (g === 'strength') return 'Strength';
  if (g === 'muscle') return 'Muscle gain';
  if (g === 'weight_loss') return 'Weight loss';
  if (g === 'general') return 'General fitness';
  return goal;
}

export const TimelineDetailsScreen: React.FC = () => {
  const { isOnline } = useOfflineCache();
  const {
    latest,
    history,
    loading,
    error,
    refetch,
  } = useTransformationPredictions(isOnline);
  const [refreshing, setRefreshing] = React.useState(false);
  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch(true); // recompute so timeline reflects latest goal & consistency
    setRefreshing(false);
  }, [refetch]);

  // Refetch and recompute when user opens this screen so goal/workout changes show up
  useFocusEffect(
    React.useCallback(() => {
      if (isOnline) refetch(true);
    }, [isOnline, refetch])
  );

  if (loading && !latest) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading timeline…</Text>
      </View>
    );
  }

  if (error && !latest) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={refetch}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!latest) {
    return (
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Text style={styles.emptyTitle}>No timeline yet</Text>
        <Text style={styles.emptySubtitle}>
          Pull to refresh to generate your transformation timeline based on your
          training consistency.
        </Text>
      </ScrollView>
    );
  }

  const goalLabel = formatGoalLabel(latest.primary_goal);

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.screenTitle}>Your Transformation Timeline</Text>
      {goalLabel ? (
        <Text style={styles.goalSubtitle}>Based on your goal: {goalLabel}</Text>
      ) : null}
      <PredictionCard prediction={latest} />
      <DeltaIndicator prediction={latest} />
      {history.length > 1 ? (
        <View style={styles.historySection}>
          <Text style={styles.historyTitle}>Past predictions</Text>
          {history
            .filter((p) => p.id !== latest.id)
            .slice(0, 10)
            .map((p) => (
              <HistoryRow key={p.id} prediction={p} />
            ))}
        </View>
      ) : null}
    </ScrollView>
  );
};

function HistoryRow({ prediction }: { prediction: TransformationPrediction }) {
  const date = new Date(prediction.computed_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const strength = prediction.strength_gain_weeks ?? '—';
  const visible = prediction.visible_change_weeks ?? '—';
  return (
    <View style={styles.historyRow}>
      <Text style={styles.historyDate}>{date}</Text>
      <Text style={styles.historyMeta}>
        Strength: {typeof strength === 'number' ? `${strength} wk` : strength} · Visible:{' '}
        {typeof visible === 'number' ? `${visible} wk` : visible}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  container: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingText: { marginTop: 12, fontSize: 16, color: '#666' },
  errorText: { fontSize: 16, color: '#c00', textAlign: 'center' },
  retryButton: {
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  screenTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111',
    marginBottom: 8,
  },
  goalSubtitle: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 15,
    color: '#666',
    lineHeight: 22,
  },
  historySection: {
    marginTop: 8,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111',
  },
  historyRow: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  historyDate: { fontSize: 14, fontWeight: '500', color: '#111' },
  historyMeta: { fontSize: 13, color: '#666', marginTop: 2 },
});
