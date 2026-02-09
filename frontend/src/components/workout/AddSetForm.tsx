/**
 * Add Set Form component.
 * Modal form for adding a new set to an exercise.
 */
import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Picker } from '@react-native-picker/picker';
import { SetType, RPE } from '../../types/workout.types';

const getSetTypeColor = (setType: SetType): string => {
  switch (setType) {
    case SetType.WORKING:
      return '#007AFF';
    case SetType.WARMUP:
      return '#FF9500';
    case SetType.FAILURE:
      return '#FF3B30';
    case SetType.DROP:
      return '#AF52DE';
    case SetType.AMRAP:
      return '#34C759';
    default:
      return '#8E8E93';
  }
};
import { useUserStore } from '../../store/userStore';
import { convertWeightToKg, getUnitLabel } from '../../utils/units';

interface AddSetFormProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (data: {
    reps?: number;
    weight?: number;
    duration_seconds?: number;
    set_type: SetType;
    rpe?: RPE;
    rest_time_seconds?: number;
  }) => Promise<void>;
}

export const AddSetForm: React.FC<AddSetFormProps> = ({
  visible,
  onClose,
  onSubmit,
}) => {
  const insets = useSafeAreaInsets();
  const userProfile = useUserStore((state) => state.userProfile);
  const userUnit = userProfile?.units || 'kg';
  const unitLabel = getUnitLabel(userUnit);

  const [reps, setReps] = useState<string>('');
  const [weight, setWeight] = useState<string>('');
  const [duration, setDuration] = useState<string>('');
  const [setType, setSetType] = useState<SetType>(SetType.WORKING);
  const [rpe, setRpe] = useState<RPE | undefined>(undefined);
  const [restTime, setRestTime] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);

    // Validation: must include at least one of reps, weight, or duration_seconds
    // This matches backend validation: "Set must include at least one of: reps, weight, or duration_seconds"
    if (!reps && !weight && !duration) {
      setError('Please enter at least reps, weight, or duration');
      return;
    }

    try {
      setLoading(true);
      await onSubmit({
        reps: reps ? parseInt(reps, 10) : undefined,
        weight: weight ? convertWeightToKg(parseFloat(weight), userUnit) : undefined,
        duration_seconds: duration ? parseInt(duration, 10) : undefined,
        set_type: setType,
        rpe: rpe,
        rest_time_seconds: restTime ? parseInt(restTime, 10) : undefined,
      });
      
      // Reset form
      setReps('');
      setWeight('');
      setDuration('');
      setSetType(SetType.WORKING);
      setRpe(undefined);
      setRestTime('');
      onClose();
    } catch (err: any) {
      console.error('Error adding set:', err);
      let errorMessage = 'Failed to add set';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    setReps('');
    setWeight('');
    setDuration('');
    setSetType(SetType.WORKING);
    setRpe(undefined);
    setRestTime('');
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
      statusBarTranslucent
    >
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Add Set</Text>
          <TouchableOpacity onPress={handleClose}>
            <Text style={styles.closeButton}>Close</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Hevy-like: Reps + Weight on same row */}
          <View style={styles.rowSection}>
            <View style={styles.halfField}>
              <Text style={styles.label}>Reps</Text>
              <TextInput
                style={styles.input}
                placeholder="Reps"
                placeholderTextColor="#999"
                value={reps}
                onChangeText={setReps}
                keyboardType="number-pad"
              />
            </View>
            <View style={styles.halfField}>
              <Text style={styles.label}>Weight ({unitLabel})</Text>
              <TextInput
                style={styles.input}
                placeholder={unitLabel}
                placeholderTextColor="#999"
                value={weight}
                onChangeText={setWeight}
                keyboardType="decimal-pad"
              />
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Set Type</Text>
            <View style={styles.chipContainer}>
              <TouchableOpacity
                style={[
                  styles.chip,
                  setType === SetType.WARMUP && styles.chipSelected,
                  { backgroundColor: setType === SetType.WARMUP ? getSetTypeColor(SetType.WARMUP) : '#f0f0f0' }
                ]}
                onPress={() => setSetType(SetType.WARMUP)}
              >
                <Text style={[
                  styles.chipText,
                  setType === SetType.WARMUP && styles.chipTextSelected
                ]}>
                  Warmup
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.chip,
                  setType === SetType.WORKING && styles.chipSelected,
                  { backgroundColor: setType === SetType.WORKING ? getSetTypeColor(SetType.WORKING) : '#f0f0f0' }
                ]}
                onPress={() => setSetType(SetType.WORKING)}
              >
                <Text style={[
                  styles.chipText,
                  setType === SetType.WORKING && styles.chipTextSelected
                ]}>
                  Working
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.chip,
                  setType === SetType.FAILURE && styles.chipSelected,
                  { backgroundColor: setType === SetType.FAILURE ? getSetTypeColor(SetType.FAILURE) : '#f0f0f0' }
                ]}
                onPress={() => setSetType(SetType.FAILURE)}
              >
                <Text style={[
                  styles.chipText,
                  setType === SetType.FAILURE && styles.chipTextSelected
                ]}>
                  Failure
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.chip,
                  setType === SetType.DROP && styles.chipSelected,
                  { backgroundColor: setType === SetType.DROP ? getSetTypeColor(SetType.DROP) : '#f0f0f0' }
                ]}
                onPress={() => setSetType(SetType.DROP)}
              >
                <Text style={[
                  styles.chipText,
                  setType === SetType.DROP && styles.chipTextSelected
                ]}>
                  Drop
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.chip,
                  setType === SetType.AMRAP && styles.chipSelected,
                  { backgroundColor: setType === SetType.AMRAP ? getSetTypeColor(SetType.AMRAP) : '#f0f0f0' }
                ]}
                onPress={() => setSetType(SetType.AMRAP)}
              >
                <Text style={[
                  styles.chipText,
                  setType === SetType.AMRAP && styles.chipTextSelected
                ]}>
                  AMRAP
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Optional: Duration */}
          <View style={styles.section}>
            <Text style={styles.labelOptional}>Duration (seconds, optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Time-based exercises"
              placeholderTextColor="#999"
              value={duration}
              onChangeText={setDuration}
              keyboardType="number-pad"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.labelOptional}>RPE (Optional)</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={rpe || ''}
                onValueChange={(value) => setRpe(value || undefined)}
                style={styles.picker}
              >
                <Picker.Item label="None" value="" />
                <Picker.Item label="Easy" value={RPE.EASY} />
                <Picker.Item label="Medium" value={RPE.MEDIUM} />
                <Picker.Item label="Hard" value={RPE.HARD} />
              </Picker>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.labelOptional}>Rest (seconds, optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Rest time"
              placeholderTextColor="#999"
              value={restTime}
              onChangeText={setRestTime}
              keyboardType="number-pad"
            />
          </View>
        </ScrollView>

        <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom, 16) }]}>
          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
            activeOpacity={0.8}
          >
            <Text style={styles.submitButtonText}>
              {loading ? 'Adding...' : 'Add Set'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e8e8e8',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  closeButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 12,
  },
  errorContainer: {
    backgroundColor: '#fee',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 14,
  },
  rowSection: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  halfField: {
    flex: 1,
  },
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  labelOptional: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
    marginBottom: 6,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    paddingHorizontal: 14,
    fontSize: 16,
    backgroundColor: '#fafafa',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    backgroundColor: '#fafafa',
  },
  picker: {
    height: 48,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
    gap: 8,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    minWidth: 80,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipSelected: {
    borderWidth: 0,
  },
  chipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: '#fff',
    fontWeight: '700',
  },
  footer: {
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#e8e8e8',
    backgroundColor: '#fff',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#999',
    opacity: 0.8,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
});
