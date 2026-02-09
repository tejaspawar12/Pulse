/**
 * Coach tab: today's commitment + coach message + chat with coach.
 * Coach uses only real stored data (metrics, profile, workout history) from the backend.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { useCoach } from '../hooks/useCoach';
import { CommitmentCard } from '../components/log/CommitmentCard';
import { CoachTodayCard } from '../components/log/CoachTodayCard';
import { StatusChipsRow } from '../components/log/StatusChipsRow';
import { GoalLabel } from '../components/common/GoalLabel';
import { coachApi, type CoachChatMessage } from '../services/api/coach.api';

export const CoachScreen: React.FC = () => {
  const { isOnline } = useOfflineCache();
  const { commitment, coach, metrics, loading, error, refetch } = useCoach(isOnline);

  const [chatMessages, setChatMessages] = useState<CoachChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [sending, setSending] = useState(false);

  const loadChatHistory = useCallback(async () => {
    if (!isOnline) {
      setChatLoading(false);
      return;
    }
    setChatLoading(true);
    try {
      const list = await coachApi.getChatHistory(50);
      setChatMessages(list);
    } catch {
      setChatMessages([]);
    } finally {
      setChatLoading(false);
    }
  }, [isOnline]);

  useFocusEffect(
    useCallback(() => {
      loadChatHistory();
    }, [loadChatHistory])
  );

  const handleSendChat = async () => {
    const text = chatInput.trim();
    if (!text || !isOnline || sending) return;
    setChatInput('');
    setSending(true);
    const userMessage: CoachChatMessage = {
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);
    try {
      const { reply } = await coachApi.sendChatMessage(text);
      const assistantMessage: CoachChatMessage = {
        role: 'assistant',
        content: reply || 'No reply.',
        created_at: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Failed to send. Please try again.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  if (loading && !commitment.commitment && !coach.message) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading coach...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={false}
      >
        <GoalLabel />
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today</Text>
          <Text style={styles.hint}>
            Coach uses your real data: commitment, workout history, and metrics.
          </Text>
          <CommitmentCard
            commitment={commitment}
            disabled={!isOnline}
            onCommitSuccess={refetch}
          />
          {metrics.consistencyScore !== null || metrics.momentumTrend || metrics.dropoutRisk || metrics.burnoutRisk ? (
            <StatusChipsRow metrics={metrics} />
          ) : null}
          <CoachTodayCard
            coach={coach}
            disabled={!isOnline}
            onRetry={refetch}
            onStartTrial={() => {}}
          />
        </View>

        <View style={styles.chatSection}>
          <Text style={styles.sectionTitle}>Chat with Coach</Text>
          <Text style={styles.hint}>
            Ask about your training, consistency, or next steps. Coach answers using your real data only.
          </Text>
          {chatLoading ? (
            <View style={styles.chatLoadingWrap}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.chatLoadingText}>Loading chat...</Text>
            </View>
          ) : chatMessages.length === 0 ? (
            <Text style={styles.chatEmpty}>No messages yet. Say hi or ask a question below.</Text>
          ) : (
            <View style={styles.chatList}>
              {chatMessages.map((item, i) => {
                const isUser = item.role === 'user';
                return (
                  <View
                    key={`chat-${i}`}
                    style={[styles.chatBubbleWrap, isUser ? styles.chatBubbleWrapUser : styles.chatBubbleWrapAssistant]}
                  >
                    <View style={[styles.chatBubble, isUser ? styles.chatBubbleUser : styles.chatBubbleAssistant]}>
                      <Text style={[styles.chatBubbleText, isUser ? styles.chatBubbleTextUser : styles.chatBubbleTextAssistant]}>
                        {item.content}
                      </Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}
        </View>

        {error ? (
          <View style={styles.errorRow}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={() => refetch()} disabled={!isOnline}>
              <Text style={styles.retryButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.chatInputRow}>
        <TextInput
          style={styles.chatInput}
          placeholder={isOnline ? "Ask the coach..." : "Offline"}
          placeholderTextColor="#999"
          value={chatInput}
          onChangeText={setChatInput}
          editable={isOnline}
          multiline
          maxLength={1000}
          onSubmitEditing={handleSendChat}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!isOnline || sending || !chatInput.trim()) && styles.sendButtonDisabled]}
          onPress={handleSendChat}
          disabled={!isOnline || sending || !chatInput.trim()}
        >
          {sending ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 100 },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  loadingText: { marginTop: 12, fontSize: 16, color: '#666' },
  section: { marginBottom: 24 },
  chatSection: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8, color: '#111' },
  hint: { fontSize: 13, color: '#666', marginBottom: 12 },
  chatLoadingWrap: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 16 },
  chatLoadingText: { fontSize: 14, color: '#666' },
  chatList: { paddingVertical: 8 },
  chatEmpty: { fontSize: 14, color: '#999', textAlign: 'center', paddingVertical: 24 },
  chatBubbleWrap: { flexDirection: 'row', marginBottom: 10 },
  chatBubbleWrapUser: { justifyContent: 'flex-end' },
  chatBubbleWrapAssistant: { justifyContent: 'flex-start' },
  chatBubble: { maxWidth: '82%', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18 },
  chatBubbleUser: { backgroundColor: '#007AFF', borderBottomRightRadius: 4 },
  chatBubbleAssistant: { backgroundColor: '#e9e9eb', borderBottomLeftRadius: 4 },
  chatBubbleText: {
    fontSize: 15,
    padding: 0,
    margin: 0,
    borderWidth: 0,
    ...(Platform.OS === 'android' && { textAlignVertical: 'center' }),
  },
  chatBubbleTextUser: { color: '#fff' },
  chatBubbleTextAssistant: { color: '#111' },
  chatInputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingBottom: Platform.OS === 'ios' ? 28 : 10,
    backgroundColor: '#fff',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#ccc',
  },
  chatInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 20,
    fontSize: 16,
    color: '#111',
    marginRight: 10,
  },
  sendButton: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 20,
    minWidth: 60,
  },
  sendButtonDisabled: { opacity: 0.5 },
  sendButtonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  errorRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 8 },
  errorText: { flex: 1, fontSize: 14, color: '#c00' },
  retryButton: { paddingVertical: 8, paddingHorizontal: 16, backgroundColor: '#007AFF', borderRadius: 8 },
  retryButtonText: { color: '#fff', fontWeight: '600' },
});
