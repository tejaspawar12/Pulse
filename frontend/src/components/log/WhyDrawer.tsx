/**
 * WhyDrawer: modal showing reasons (reason_key, reason_label) from metrics (Phase 2 Week 5 Day 5).
 */
import React from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet, ScrollView, Pressable } from 'react-native';

interface Reason {
  reason_key: string;
  reason_label: string;
}

interface WhyDrawerProps {
  visible: boolean;
  onClose: () => void;
  reasons: Reason[];
}

export const WhyDrawer: React.FC<WhyDrawerProps> = ({ visible, onClose, reasons }) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.drawer} onPress={(e) => e.stopPropagation()}>
          <View style={styles.handle} />
          <Text style={styles.title}>Why this score?</Text>
          <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
            {reasons.length === 0 ? (
              <Text style={styles.empty}>No details available.</Text>
            ) : (
              reasons.map((r) => (
                <View key={r.reason_key} style={styles.reasonRow}>
                  <Text style={styles.reasonLabel}>{r.reason_label}</Text>
                </View>
              ))
            )}
          </ScrollView>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeButtonText}>Close</Text>
          </TouchableOpacity>
        </Pressable>
      </Pressable>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  drawer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 20,
    paddingBottom: 32,
    maxHeight: '70%',
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: '#ddd',
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  list: {
    maxHeight: 300,
  },
  listContent: {
    paddingBottom: 16,
  },
  empty: {
    fontSize: 14,
    color: '#999',
  },
  reasonRow: {
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  reasonLabel: {
    fontSize: 15,
    color: '#333',
  },
  closeButton: {
    marginTop: 16,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 10,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
