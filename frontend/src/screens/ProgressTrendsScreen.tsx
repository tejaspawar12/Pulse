/**
 * Progress & Trends Screen — Stats summary, streak, volume chart.
 * Phase 2 Week 3 Day 4: PeriodSelector, StatsSummaryCard, StreakCard, ProgressChart.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useStats, PeriodDays } from '../hooks/useStats';
import { useUserUnit } from '../hooks/useUserUnit';
import { PeriodSelector } from '../components/stats/PeriodSelector';
import { StatsSummaryCard } from '../components/stats/StatsSummaryCard';
import { StreakCard } from '../components/stats/StreakCard';
import { ProgressChart } from '../components/stats/ProgressChart';

export const ProgressTrendsScreen: React.FC = () => {
  const [period, setPeriod] = useState<PeriodDays>(30);
  const units = useUserUnit();
  const { summary, streak, volume, loading, error, refetch } = useStats(period);

  if (loading && !summary && !streak && !volume) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading stats...</Text>
      </View>
    );
  }

  if (error && !summary && !streak && !volume) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={refetch}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.periodWrap}>
        <PeriodSelector value={period} onChange={setPeriod} />
      </View>

      <StatsSummaryCard summary={summary ?? null} units={units} />

      <StreakCard
        current={streak?.current_streak_days ?? 0}
        longest={streak?.longest_streak_days ?? 0}
        lastWorkoutDate={streak?.last_workout_date ?? null}
      />

      <ProgressChart
        data={volume?.data ?? []}
        periodDays={period}
        units={units}
      />

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Trends narrative</Text>
        <Text style={styles.placeholderText}>Coming soon</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  periodWrap: {
    marginBottom: 16,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 14,
    color: '#666',
  },
});
