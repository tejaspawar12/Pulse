/**
 * PlanDetailsScreen: Your Training Plan — summary, this week's adjustment,
 * "Why this change?" (bullets + metrics_snapshot), auto-adjust toggle, history (Phase 2 Week 7).
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
  Switch,
  Alert,
} from 'react-native';
import { usePlan } from '../hooks/usePlan';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { PlanSummaryCard } from '../components/plan/PlanSummaryCard';
import { PlanChangeBullets } from '../components/plan/PlanChangeBullets';
import { AdjustmentMetricSnapshot } from '../components/plan/AdjustmentMetricSnapshot';
import { AdjustmentHistoryList } from '../components/plan/AdjustmentHistoryList';
import { EditPlanModal } from '../components/plan/EditPlanModal';
import { GoalLabel } from '../components/common/GoalLabel';
import type { PlanAdjustment, PlanPreferencesUpdate } from '../services/api/plan.api';

function adjustmentCardTitle(adj: PlanAdjustment): string {
  if (adj.explanation_title) return adj.explanation_title;
  if (adj.is_deload) return 'Deload week';
  return 'Plan updated';
}

export const PlanDetailsScreen: React.FC = () => {
  const { isOnline } = useOfflineCache();
  const {
    plan,
    thisWeekAdjustment,
    history,
    loading,
    error,
    noPlan,
    refetch,
    createPlan,
    updatePreferences,
    updatingPreferences,
    creating,
  } = usePlan(isOnline);

  const [refreshing, setRefreshing] = React.useState(false);
  const [editModalVisible, setEditModalVisible] = React.useState(false);
  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleCreatePlan = React.useCallback(async () => {
    const created = await createPlan();
    if (!created && error) {
      Alert.alert('Error', error);
    }
  }, [createPlan, error]);

  const handleAutoAdjustToggle = React.useCallback(
    async (value: boolean) => {
      const updated = await updatePreferences({ auto_adjust_enabled: value });
      if (!updated && error) {
        Alert.alert('Error', error);
      }
    },
    [updatePreferences, error]
  );

  const handleSavePreferences = React.useCallback(
    async (body: PlanPreferencesUpdate): Promise<boolean> => {
      const updated = await updatePreferences(body);
      return updated != null;
    },
    [updatePreferences]
  );

  if (loading && !plan && !noPlan) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading plan…</Text>
      </View>
    );
  }

  if (noPlan && !plan) {
    return (
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <GoalLabel />
        <Text style={styles.emptyTitle}>No plan yet</Text>
        <Text style={styles.emptySubtitle}>
          Create a plan to get started. We'll seed it from your coach profile or
          defaults.
        </Text>
        <TouchableOpacity
          style={[styles.button, creating && styles.buttonDisabled]}
          onPress={handleCreatePlan}
          disabled={creating}
        >
          {creating ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Create plan</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    );
  }

  if (error && !plan) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={refetch}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <GoalLabel />
      <View style={styles.titleRow}>
        <Text style={styles.screenTitle}>Your Training Plan</Text>
        {plan && (
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => setEditModalVisible(true)}
          >
            <Text style={styles.editButtonText}>Edit plan</Text>
          </TouchableOpacity>
        )}
      </View>

      <PlanSummaryCard plan={plan ?? null} />

      <EditPlanModal
        visible={editModalVisible}
        plan={plan ?? null}
        onClose={() => setEditModalVisible(false)}
        onSave={handleSavePreferences}
      />

      {thisWeekAdjustment && (
        <View style={styles.adjustmentCard}>
          <Text style={styles.adjustmentCardTitle}>
            {adjustmentCardTitle(thisWeekAdjustment)}
          </Text>
          <PlanChangeBullets bullets={thisWeekAdjustment.explanation_bullets} />
          <AdjustmentMetricSnapshot
            metrics={thisWeekAdjustment.metrics_snapshot ?? null}
          />
        </View>
      )}

      {plan && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Auto-adjust plan weekly</Text>
            <Switch
              value={plan.auto_adjust_enabled}
              onValueChange={handleAutoAdjustToggle}
              disabled={updatingPreferences}
            />
          </View>
          <Text style={styles.autoAdjustHint}>
            When enabled, your plan can adapt weekly based on consistency,
            burnout risk, and momentum.
          </Text>
        </View>
      )}

      <AdjustmentHistoryList adjustments={history} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  container: {
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 15,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  errorText: {
    fontSize: 15,
    color: '#c00',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 8,
  },
  screenTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#111',
    flex: 1,
  },
  editButton: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  editButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  adjustmentCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  adjustmentCardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111',
    marginBottom: 8,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLabel: {
    fontSize: 15,
    color: '#333',
    flex: 1,
  },
  autoAdjustHint: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
  },
});
