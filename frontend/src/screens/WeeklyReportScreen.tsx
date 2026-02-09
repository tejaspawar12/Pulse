/**
 * WeeklyReportScreen: week summary, mistake, focus, positive signal, narrative, history (Phase 2 Week 6).
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
  Platform,
} from 'react-native';
import { useWeeklyReports } from '../hooks/useWeeklyReports';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { WeekSummaryCard } from '../components/report/WeekSummaryCard';
import { MistakeSection } from '../components/report/MistakeSection';
import { FocusSection } from '../components/report/FocusSection';
import { LearningFeedbackSection } from '../components/report/LearningFeedbackSection';
import { NarrativeCard } from '../components/report/NarrativeCard';
import { ReportHistoryList } from '../components/report/ReportHistoryList';

function formatWeekLabel(weekStart: string, weekEnd: string): string {
  const s = new Date(weekStart);
  const e = new Date(weekEnd);
  return `${s.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })} – ${e.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })}`;
}

export const WeeklyReportScreen: React.FC = () => {
  const { isOnline } = useOfflineCache();
  const {
    latest,
    history,
    loading,
    error,
    refetch,
  } = useWeeklyReports(isOnline);
  const [refreshing, setRefreshing] = React.useState(false);
  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const webMinHeight = Platform.OS === 'web' ? { minHeight: '100vh' } : {};
  const centerStyle = [styles.center, webMinHeight];

  if (loading && !latest) {
    return (
      <View style={centerStyle}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading report…</Text>
      </View>
    );
  }

  if (error && !latest) {
    return (
      <View style={centerStyle}>
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
        style={webMinHeight}
        contentContainerStyle={[styles.container, styles.emptyContainer]}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📋</Text>
          <Text style={styles.emptyTitle}>No weekly report yet</Text>
          <Text style={styles.emptySubtitle}>
            Your first report will appear after you complete at least 2 workouts
            in a single week. Reports are generated every Monday.
          </Text>
        </View>
      </ScrollView>
    );
  }

  if (latest.status === 'insufficient_data') {
    return (
      <ScrollView
        style={webMinHeight}
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Text style={styles.weekLabel}>
          {formatWeekLabel(latest.week_start, latest.week_end)}
        </Text>
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📋</Text>
          <Text style={styles.emptyTitle}>Not enough data for this week</Text>
          <Text style={styles.emptySubtitle}>
            Complete at least 2 workouts in a week to get your weekly report.
            Pull to refresh after logging more workouts.
          </Text>
        </View>
        <ReportHistoryList reports={history.filter((r) => r.id !== latest.id)} />
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={webMinHeight}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.weekLabel}>
        {formatWeekLabel(latest.week_start, latest.week_end)}
      </Text>
      <WeekSummaryCard report={latest} />
      <MistakeSection report={latest} />
      <FocusSection report={latest} />
      <LearningFeedbackSection report={latest} />
      <NarrativeCard report={latest} />
      <ReportHistoryList
        reports={history.filter((r) => r.id !== latest.id)}
      />
    </ScrollView>
  );
};

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
  weekLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  emptyContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingVertical: 24,
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    marginHorizontal: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 15,
    color: '#666',
    lineHeight: 22,
    textAlign: 'center',
  },
});
