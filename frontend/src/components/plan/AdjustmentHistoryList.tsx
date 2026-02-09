/**
 * AdjustmentHistoryList: list of past adjustments (Phase 2 Week 7).
 * Expandable rows: tap "View details" to show full bullets + metrics snapshot.
 */
import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { PlanChangeBullets } from './PlanChangeBullets';
import { AdjustmentMetricSnapshot } from './AdjustmentMetricSnapshot';
import type { PlanAdjustment } from '../../services/api/plan.api';

interface AdjustmentHistoryListProps {
  adjustments: PlanAdjustment[];
}

function formatWeekLabel(weekStart: string): string {
  const d = new Date(weekStart);
  const end = new Date(d);
  end.setDate(end.getDate() + 6);
  return `${d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })} – ${end.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })}`;
}

function summaryForAdjustment(adj: PlanAdjustment): string {
  if (adj.explanation_title) return adj.explanation_title;
  if (adj.is_deload) return 'Deload week';
  if (adj.trigger_reason === 'burnout') return 'Deload (burnout)';
  if (adj.trigger_reason === 'slipping') return 'Volume reduced';
  if (adj.trigger_reason === 'momentum_up') return 'Volume increased';
  if (adj.trigger_reason === 'plateau') return 'Plan updated';
  return 'Plan updated';
}

export const AdjustmentHistoryList: React.FC<AdjustmentHistoryListProps> = ({
  adjustments,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!adjustments.length) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.title}>Recent changes</Text>
      <FlatList
        data={adjustments}
        keyExtractor={(item) => item.id}
        scrollEnabled={false}
        renderItem={({ item }) => {
          const isExpanded = expandedId === item.id;
          const hasDetails =
            (item.explanation_bullets && item.explanation_bullets.length > 0) ||
            item.metrics_snapshot;
          return (
            <View style={styles.row}>
              <Text style={styles.weekLabel}>{formatWeekLabel(item.week_start)}</Text>
              <Text style={styles.summary}>{summaryForAdjustment(item)}</Text>
              {item.explanation_bullets?.[0] && !isExpanded && (
                <Text style={styles.bulletPreview} numberOfLines={1}>
                  {item.explanation_bullets[0]}
                </Text>
              )}
              {hasDetails && (
                <TouchableOpacity
                  style={styles.detailsToggle}
                  onPress={() => setExpandedId(isExpanded ? null : item.id)}
                >
                  <Text style={styles.detailsToggleText}>
                    {isExpanded ? 'Hide details' : 'View details'}
                  </Text>
                </TouchableOpacity>
              )}
              {isExpanded && (
                <View style={styles.detailsBlock}>
                  <PlanChangeBullets bullets={item.explanation_bullets} />
                  <AdjustmentMetricSnapshot
                    metrics={item.metrics_snapshot ?? null}
                  />
                </View>
              )}
            </View>
          );
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    marginTop: 8,
    marginBottom: 24,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111',
  },
  row: {
    paddingVertical: 12,
    paddingHorizontal: 0,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  weekLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111',
  },
  summary: {
    fontSize: 13,
    color: '#007AFF',
    marginTop: 4,
    fontWeight: '500',
  },
  bulletPreview: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  detailsToggle: {
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  detailsToggleText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  detailsBlock: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#eee',
  },
});
