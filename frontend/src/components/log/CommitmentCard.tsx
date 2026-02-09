/**
 * CommitmentCard: today's commitment state; Yes / No / Reschedule (Phase 2 Week 5 Day 5).
 */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import type { CommitmentState } from '../../hooks/useCoach';
import { accountabilityApi, type CommitPayload } from '../../services/api/accountability.api';

interface CommitmentCardProps {
  commitment: CommitmentState;
  disabled?: boolean;
  onCommitSuccess?: () => void;
}

export const CommitmentCard: React.FC<CommitmentCardProps> = ({
  commitment,
  disabled = false,
  onCommitSuccess,
}) => {
  const [submitting, setSubmitting] = useState<'yes' | 'no' | 'reschedule' | null>(null);

  const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);

  const handleCommit = async (payload: CommitPayload) => {
    if (disabled) return;
    const key = payload.status === 'yes' ? 'yes' : payload.status === 'no' ? 'no' : 'reschedule';
    setSubmitting(key);
    try {
      await accountabilityApi.commitToday(payload);
      onCommitSuccess?.();
    } catch (err) {
      console.error('Commit failed:', err);
    } finally {
      setSubmitting(null);
    }
  };

  const isDisabled = disabled || submitting !== null;
  const hasCommitted = commitment.status !== null;

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Today&apos;s commitment</Text>
      {commitment.completed ? (
        <View style={styles.completedRow}>
          <Text style={styles.completedText}>✓ Completed</Text>
        </View>
      ) : hasCommitted ? (
        <View style={styles.statusRow}>
          <Text style={styles.statusText}>
            {commitment.status === 'yes' && 'I\'ll work out today'}
            {commitment.status === 'no' && 'Not today'}
            {commitment.status === 'rescheduled' && 'Rescheduled'}
          </Text>
          {!commitment.completed && (
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.btn, styles.btnSecondary, isDisabled && styles.btnDisabled]}
                onPress={() => handleCommit({ status: 'yes' })}
                disabled={isDisabled}
              >
                {submitting === 'yes' ? <ActivityIndicator size="small" color="#007AFF" /> : <Text style={styles.btnTextSecondary}>Yes</Text>}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, styles.btnSecondary, isDisabled && styles.btnDisabled]}
                onPress={() => handleCommit({ status: 'no' })}
                disabled={isDisabled}
              >
                {submitting === 'no' ? <ActivityIndicator size="small" color="#007AFF" /> : <Text style={styles.btnTextSecondary}>No</Text>}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, styles.btnSecondary, isDisabled && styles.btnDisabled]}
                onPress={() => handleCommit({ status: 'rescheduled', rescheduled_to_date: tomorrow, rescheduled_to_time: '18:00' })}
                disabled={isDisabled}
              >
                {submitting === 'reschedule' ? <ActivityIndicator size="small" color="#007AFF" /> : <Text style={styles.btnTextSecondary}>Reschedule</Text>}
              </TouchableOpacity>
            </View>
          )}
        </View>
      ) : (
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.btn, styles.btnYes, isDisabled && styles.btnDisabled]}
            onPress={() => handleCommit({ status: 'yes' })}
            disabled={isDisabled}
          >
            {submitting === 'yes' ? <ActivityIndicator size="small" color="#fff" /> : <Text style={styles.btnText}>Yes</Text>}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.btnNo, isDisabled && styles.btnDisabled]}
            onPress={() => handleCommit({ status: 'no' })}
            disabled={isDisabled}
          >
            {submitting === 'no' ? <ActivityIndicator size="small" color="#fff" /> : <Text style={styles.btnText}>No</Text>}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.btnReschedule, isDisabled && styles.btnDisabled]}
            onPress={() => handleCommit({ status: 'rescheduled', rescheduled_to_date: tomorrow, rescheduled_to_time: '18:00' })}
            disabled={isDisabled}
          >
            {submitting === 'reschedule' ? <ActivityIndicator size="small" color="#fff" /> : <Text style={styles.btnText}>Reschedule</Text>}
          </TouchableOpacity>
        </View>
      )}
      {disabled && (
        <Text style={styles.hint}>Go online to update commitment.</Text>
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
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  completedRow: {
    paddingVertical: 8,
  },
  completedText: {
    fontSize: 15,
    color: '#34C759',
    fontWeight: '500',
  },
  statusRow: {
    paddingVertical: 4,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
  },
  btn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  btnYes: {
    backgroundColor: '#34C759',
  },
  btnNo: {
    backgroundColor: '#8E8E93',
  },
  btnReschedule: {
    backgroundColor: '#007AFF',
  },
  btnSecondary: {
    backgroundColor: '#f0f0f0',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  btnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  btnTextSecondary: {
    color: '#333',
    fontSize: 14,
    fontWeight: '600',
  },
  hint: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
});
