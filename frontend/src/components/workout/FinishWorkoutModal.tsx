/**
 * Finish Workout Modal Component
 * Allows user to select completion status and add notes before finishing workout
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CompletionStatus } from '../../types/workout.types';

interface FinishWorkoutModalProps {
  visible: boolean;
  onClose: () => void;
  onFinish: (completionStatus: CompletionStatus, notes?: string) => void;
  loading?: boolean;
}

export const FinishWorkoutModal: React.FC<FinishWorkoutModalProps> = ({
  visible,
  onClose,
  onFinish,
  loading = false
}) => {
  const insets = useSafeAreaInsets();
  const [completionStatus, setCompletionStatus] = useState<CompletionStatus>(
    CompletionStatus.COMPLETED
  );
  const [notes, setNotes] = useState('');

  const handleFinish = () => {
    onFinish(completionStatus, notes.trim() || undefined);
  };

  const bottomPadding = Math.max(insets.bottom, 24);

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <View style={[styles.container, { paddingBottom: bottomPadding }]}>
          <Text style={styles.title}>Finish Workout</Text>

          {/* Completion Status Selection */}
          <View style={styles.statusContainer}>
            <TouchableOpacity
              style={[
                styles.statusButton,
                completionStatus === CompletionStatus.COMPLETED &&
                  styles.statusButtonActive
              ]}
              onPress={() => setCompletionStatus(CompletionStatus.COMPLETED)}
              disabled={loading}
            >
              <Text
                style={[
                  styles.statusButtonText,
                  completionStatus === CompletionStatus.COMPLETED &&
                    styles.statusButtonTextActive
                ]}
              >
                Completed
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.statusButton,
                completionStatus === CompletionStatus.PARTIAL &&
                  styles.statusButtonActive
              ]}
              onPress={() => setCompletionStatus(CompletionStatus.PARTIAL)}
              disabled={loading}
            >
              <Text
                style={[
                  styles.statusButtonText,
                  completionStatus === CompletionStatus.PARTIAL &&
                    styles.statusButtonTextActive
                ]}
              >
                Partial
              </Text>
            </TouchableOpacity>
          </View>

          {/* Notes Input */}
          <Text style={styles.notesLabel}>Notes (optional)</Text>
          <TextInput
            style={styles.notesInput}
            placeholder="Add notes about your workout..."
            multiline
            numberOfLines={4}
            value={notes}
            onChangeText={setNotes}
            maxLength={2000}
            editable={!loading}
            placeholderTextColor="#999"
          />

          {/* Buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
              disabled={loading}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.button,
                styles.finishButton,
                loading && styles.buttonDisabled
              ]}
              onPress={handleFinish}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.finishButtonText}>Finish Workout</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end'
  },
  container: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center'
  },
  statusContainer: {
    flexDirection: 'row',
    marginBottom: 20,
    gap: 10
  },
  statusButton: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ddd',
    alignItems: 'center',
    backgroundColor: '#f5f5f5'
  },
  statusButtonActive: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD'
  },
  statusButtonText: {
    fontSize: 16,
    color: '#666'
  },
  statusButtonTextActive: {
    color: '#007AFF',
    fontWeight: '600'
  },
  notesLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333'
  },
  notesInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 20
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 10
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center'
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ddd'
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600'
  },
  finishButton: {
    backgroundColor: '#007AFF'
  },
  finishButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600'
  },
  buttonDisabled: {
    opacity: 0.6
  }
});
