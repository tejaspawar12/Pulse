/**
 * Insights Screen — metrics from GET /metrics/summary, AI insight from GET /ai/insights.
 * Single mode: one consistent experience for all users.
 */
import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  RefreshControl,
  LayoutChangeEvent,
} from 'react-native';
import { metricsApi } from '../services/api/metrics.api';
import { aiApi } from '../services/api/ai.api';
import type { MetricsSummary } from '../services/api/metrics.api';
import type { AIInsights } from '../services/api/ai.api';

type Period = 7 | 30;

function errorDetailToString(detail: unknown): string {
  if (detail == null) return 'Something went wrong';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((d: { msg?: string }) => (d?.msg != null ? String(d.msg) : ''));
    return messages.length ? messages.join('. ') : 'Validation error';
  }
  if (typeof detail === 'object' && detail !== null && 'msg' in detail) return String((detail as { msg: string }).msg);
  return 'Something went wrong';
}

export const InsightsScreen: React.FC = () => {
  const [period, setPeriod] = useState<Period>(7);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [insights, setInsights] = useState<AIInsights | null>(null);
  const [usage, setUsage] = useState<{ insights_remaining_today: number; insights_limit_per_day: number } | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadMetrics = useCallback(async (days: Period) => {
    setLoadingMetrics(true);
    setError(null);
    try {
      const data = await metricsApi.getSummary(days);
      setMetrics(data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      setError(errorDetailToString(err.response?.data?.detail) || 'Failed to load metrics');
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  const loadUsage = useCallback(async () => {
    setLoadingUsage(true);
    try {
      const data = await aiApi.getUsage();
      setUsage({ insights_remaining_today: data.insights_remaining_today, insights_limit_per_day: data.insights_limit_per_day });
    } catch {
      setUsage(null);
    } finally {
      setLoadingUsage(false);
    }
  }, []);

  const scrollViewRef = useRef<ScrollView>(null);
  const insightSectionLayout = useRef({ y: 0, height: 0 });

  const loadInsights = useCallback(async () => {
    setLoadingInsights(true);
    setError(null);
    try {
      const data = await aiApi.getInsights(period);
      // Normalize response: ensure arrays and strings exist so the card always renders
      const normalized: AIInsights = {
        summary: typeof data.summary === 'string' && data.summary.trim() ? data.summary : 'Your training summary is ready.',
        strengths: Array.isArray(data.strengths) ? data.strengths : [],
        gaps: Array.isArray(data.gaps) ? data.gaps : [],
        next_workout: Array.isArray(data.next_workout) ? data.next_workout : [],
        progression_rule: typeof data.progression_rule === 'string' && data.progression_rule.trim() ? data.progression_rule : 'Add weight or reps when you hit the top of your rep range.',
      };
      setInsights(normalized);
      await loadUsage();
      // Scroll to insight card so it's visible after generation
      requestAnimationFrame(() => {
        scrollViewRef.current?.scrollTo({
          y: insightSectionLayout.current.y - 24,
          animated: true,
        });
      });
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: unknown } } };
      if (err.response?.status === 429) {
        setError('AI insights limit reached for today. Try again tomorrow.');
      } else {
        setError(errorDetailToString(err.response?.data?.detail) || 'Failed to generate insight');
      }
    } finally {
      setLoadingInsights(false);
    }
  }, [period, loadUsage]);

  const onPeriodChange = (days: Period) => {
    setPeriod(days);
    setInsights(null);
    loadMetrics(days);
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    await Promise.all([loadMetrics(period), loadUsage()]);
    setRefreshing(false);
  }, [period, loadMetrics, loadUsage]);

  React.useEffect(() => {
    loadMetrics(period);
    loadUsage();
  }, []);

  const onInsightSectionLayout = useCallback((e: LayoutChangeEvent) => {
    const { y } = e.nativeEvent.layout;
    insightSectionLayout.current.y = y;
  }, []);

  return (
    <ScrollView
      ref={scrollViewRef}
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.periodRow}>
        <Text style={styles.label}>Period</Text>
        <View style={styles.periodButtons}>
          <TouchableOpacity
            style={[styles.periodBtn, period === 7 && styles.periodBtnActive]}
            onPress={() => onPeriodChange(7)}
          >
            <Text style={[styles.periodBtnText, period === 7 && styles.periodBtnTextActive]}>7 days</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.periodBtn, period === 30 && styles.periodBtnActive]}
            onPress={() => onPeriodChange(30)}
          >
            <Text style={[styles.periodBtnText, period === 30 && styles.periodBtnTextActive]}>30 days</Text>
          </TouchableOpacity>
        </View>
      </View>

      {usage !== null && (
        <View style={styles.usageRow}>
          <Text style={styles.usageText}>
            AI calls remaining today: {usage.insights_remaining_today} / {usage.insights_limit_per_day}
          </Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {loadingMetrics ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading metrics…</Text>
        </View>
      ) : !loadingMetrics && !metrics ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyText}>Pull to refresh to load metrics.</Text>
        </View>
      ) : metrics ? (
        <View style={styles.metricsCard}>
          <Text style={styles.cardTitle}>Metrics</Text>
          <Text style={styles.metricLine}>Workouts: {metrics.workouts_count}</Text>
          <Text style={styles.metricLine}>Volume: {metrics.total_volume_kg.toFixed(0)} kg</Text>
          <Text style={styles.metricLine}>Per week: {metrics.workouts_per_week} workouts</Text>
          <Text style={styles.metricLine}>Streak: {metrics.streak_days} days</Text>
          {metrics.imbalance_hint && (
            <Text style={styles.hintLine}>{metrics.imbalance_hint}</Text>
          )}
        </View>
      ) : null}

      <View style={styles.insightSection} onLayout={onInsightSectionLayout}>
        {!insights && !loadingInsights && (
          <Text style={styles.hintText}>Tap below to generate your AI training insight for the selected period.</Text>
        )}
        <TouchableOpacity
          style={[styles.generateBtn, loadingInsights && styles.generateBtnDisabled]}
          onPress={loadInsights}
          disabled={loadingInsights}
        >
          {loadingInsights ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.generateBtnText}>Generate insight</Text>
          )}
        </TouchableOpacity>

        {loadingInsights && !insights && (
          <Text style={styles.loadingText}>Generating insight…</Text>
        )}

        {insights && (
          <View style={styles.insightCard}>
            <Text style={styles.cardTitle}>Summary</Text>
            <Text style={styles.summaryText}>{insights.summary}</Text>
            {insights.strengths.length > 0 && (
              <>
                <Text style={styles.sectionLabel}>Strengths</Text>
                {insights.strengths.map((s, i) => (
                  <Text key={i} style={styles.bullet}>• {s}</Text>
                ))}
              </>
            )}
            {insights.gaps.length > 0 && (
              <>
                <Text style={styles.sectionLabel}>Areas to focus</Text>
                {insights.gaps.map((g, i) => (
                  <Text key={i} style={styles.bullet}>• {g}</Text>
                ))}
              </>
            )}
            {insights.next_workout.length > 0 && (
              <>
                <Text style={styles.sectionLabel}>Next workout</Text>
                {insights.next_workout.map((n, i) => (
                  <Text key={i} style={styles.bullet}>
                    {n.exercise_name}: {n.sets_reps_guidance}
                  </Text>
                ))}
              </>
            )}
            <Text style={styles.progressionRule}>{insights.progression_rule}</Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 32 },
  periodRow: { marginBottom: 12 },
  label: { fontSize: 14, color: '#666', marginBottom: 6 },
  periodButtons: { flexDirection: 'row', gap: 8 },
  periodBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#e0e0e0',
  },
  periodBtnActive: { backgroundColor: '#007AFF' },
  periodBtnText: { fontSize: 14, color: '#333' },
  periodBtnTextActive: { color: '#fff', fontWeight: '600' },
  usageRow: { marginBottom: 12 },
  usageText: { fontSize: 13, color: '#666' },
  errorBox: { backgroundColor: '#ffebee', padding: 12, borderRadius: 8, marginBottom: 12 },
  errorText: { color: '#c62828', fontSize: 14 },
  emptyBox: { padding: 24, alignItems: 'center' },
  emptyText: { fontSize: 14, color: '#666' },
  centered: { alignItems: 'center', paddingVertical: 24 },
  loadingText: { marginTop: 8, color: '#666', fontSize: 14 },
  metricsCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  cardTitle: { fontSize: 18, fontWeight: '600', marginBottom: 12 },
  metricLine: { fontSize: 15, marginBottom: 4 },
  hintLine: { fontSize: 14, color: '#1976d2', marginTop: 8 },
  insightSection: { marginTop: 8 },
  hintText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    textAlign: 'center',
  },
  generateBtn: {
    backgroundColor: '#34C759',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16,
  },
  generateBtnDisabled: { opacity: 0.7 },
  generateBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  insightCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  summaryText: { fontSize: 15, lineHeight: 22, marginBottom: 12 },
  sectionLabel: { fontSize: 14, fontWeight: '600', color: '#333', marginTop: 12, marginBottom: 4 },
  bullet: { fontSize: 14, marginLeft: 4, marginBottom: 2 },
  progressionRule: { fontSize: 14, fontStyle: 'italic', color: '#555', marginTop: 12 },
});
