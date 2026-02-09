/**
 * CoachTodayCard: today's coach message; AI / free_tier / unavailable (Phase 2 Week 5 Day 5).
 */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import type { CoachState } from '../../hooks/useCoach';
import { coachApi } from '../../services/api/coach.api';

interface CoachTodayCardProps {
  coach: CoachState;
  disabled?: boolean;
  onRetry?: () => void;
  onStartTrial?: () => void;
}

export const CoachTodayCard: React.FC<CoachTodayCardProps> = ({
  coach,
  disabled = false,
  onRetry,
  onStartTrial,
}) => {
  const [expanded, setExpanded] = useState(true);
  const [sendingReply, setSendingReply] = useState<string | null>(null);

  const handleQuickReply = async (text: string) => {
    if (disabled || coach.source !== 'ai') return;
    setSendingReply(text);
    try {
      await coachApi.respondToMessage(text);
      onRetry?.();
    } catch (err) {
      console.error('Respond failed:', err);
    } finally {
      setSendingReply(null);
    }
  };

  if (coach.source === null) return null;

  if (coach.source === 'unavailable') {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Coach</Text>
        <Text style={styles.unavailableText}>Coach is temporarily unavailable. Retry in a minute.</Text>
        <TouchableOpacity style={styles.retryButton} onPress={onRetry} disabled={disabled}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (coach.source === 'free_tier') {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Coach</Text>
        <Text style={styles.message}>{coach.message ?? 'Your daily coaching will appear here.'}</Text>
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={onRetry}
          disabled={disabled}
        >
          <Text style={styles.ctaButtonText}>Get today&apos;s message</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ai
  return (
    <View style={styles.card}>
      <TouchableOpacity onPress={() => setExpanded(!expanded)} style={styles.header}>
        <Text style={styles.title}>Coach</Text>
        <Text style={styles.expandIcon}>{expanded ? '−' : '+'}</Text>
      </TouchableOpacity>
      {expanded && (
        <>
          <Text style={styles.message}>{coach.message ?? ''}</Text>
          {coach.oneActionStep ? (
            <Text style={styles.actionStep}>→ {coach.oneActionStep}</Text>
          ) : null}
          {coach.primaryMistake ? (
            <Text style={styles.focusLabel}>Focus: {coach.primaryMistake}</Text>
          ) : null}
          {coach.weeklyFocus ? (
            <Text style={styles.focusLabel}>This week: {coach.weeklyFocus}</Text>
          ) : null}
          {coach.quickReplies.length > 0 && (
            <View style={styles.quickReplies}>
              {coach.quickReplies.map((label) => (
                <TouchableOpacity
                  key={label}
                  style={[styles.quickReplyBtn, disabled && styles.btnDisabled]}
                  onPress={() => handleQuickReply(label)}
                  disabled={disabled || sendingReply !== null}
                >
                  {sendingReply === label ? (
                    <ActivityIndicator size="small" color="#007AFF" />
                  ) : (
                    <Text style={styles.quickReplyText}>{label}</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
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
    marginHorizontal: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  expandIcon: {
    fontSize: 18,
    color: '#666',
  },
  message: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
    marginBottom: 8,
  },
  actionStep: {
    fontSize: 14,
    color: '#007AFF',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  focusLabel: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
  },
  unavailableText: {
    fontSize: 15,
    color: '#666',
    marginBottom: 12,
  },
  retryButton: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  ctaButton: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#34C759',
    borderRadius: 8,
    marginTop: 8,
  },
  ctaButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  quickReplies: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
  },
  quickReplyBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  quickReplyText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '500',
  },
  btnDisabled: {
    opacity: 0.6,
  },
});
