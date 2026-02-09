/**
 * Edit Set Form component.
 * Modal form for editing an existing set.
 */
import React, { useState, useEffect } from 'react';
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
import { WorkoutSet, SetType, RPE } from '../../types/workout.types';

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
import { convertWeightForDisplay, convertWeightToKg, getUnitLabel } from '../../utils/units';

interface EditSetFormProps {
  visible: boolean;
  set: WorkoutSet | null;
  onClose: () => void;
  onSubmit: (setId: string, data: {
    reps?: number;
    weight?: number;
    duration_seconds?: number;
    set_type?: SetType;
    rpe?: RPE;
    rest_time_seconds?: number;
  }) => Promise<void>;
}

export const EditSetForm: React.FC<EditSetFormProps> = ({
  visible,
  set,
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

  // Pre-fill form when set changes
  useEffect(() => {
    if (set) {
      setReps(set.reps?.toString() || '');
      // Convert weight from kg to user's preferred unit for display
      const displayWeight = set.weight != null ? convertWeightForDisplay(set.weight, userUnit) : null;
      setWeight(displayWeight?.toString() || '');
      setDuration(set.duration_seconds?.toString() || '');
      setSetType(set.set_type);
      setRpe(set.rpe);
      setRestTime(set.rest_time_seconds?.toString() || '');
      setError(null);
    }
  }, [set, userUnit]);

  const handleSubmit = async () => {
    if (!set) return;

    setError(null);

    // Validation: must include at least one of reps, weight, or duration_seconds
    // This matches backend validation: "Set must include at least one of: reps, weight, or duration_seconds"
    if (!reps && !weight && !duration) {
      setError('Please enter at least reps, weight, or duration');
      return;
    }

    try {
      setLoading(true);
      await onSubmit(set.id, {
        reps: reps ? parseInt(reps, 10) : undefined,
        weight: weight ? convertWeightToKg(parseFloat(weight), userUnit) : undefined,
        duration_seconds: duration ? parseInt(duration, 10) : undefined,
        set_type: setType,
        rpe: rpe,
        rest_time_seconds: restTime ? parseInt(restTime, 10) : undefined,
      });
      
      onClose();
    } catch (err: any) {
      console.error('Error updating set:', err);
      let errorMessage = 'Failed to update set';
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
    onClose();
  };

  if (!set) return null;

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
          <Text style={styles.headerTitle}>Edit Set {set.set_number + 1}</Text>
          <TouchableOpacity onPress={handleClose}>
            <Text style={styles.closeButton}>Close</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content}>
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          <View style={styles.section}>
            <Text style={styles.label}>Reps</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter reps"
              value={reps}
              onChangeText={setReps}
              keyboardType="number-pad"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Weight ({unitLabel})</Text>
            <TextInput
              style={styles.input}
              placeholder={`Enter weight in ${unitLabel}`}
              value={weight}
              onChangeText={setWeight}
              keyboardType="decimal-pad"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Duration (seconds, optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter duration for time-based exercises"
              value={duration}
              onChangeText={setDuration}
              keyboardType="number-pad"
            />
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

          <View style={styles.section}>
            <Text style={styles.label}>RPE (Optional)</Text>
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
            <Text style={styles.label}>Rest Time (seconds, optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter rest time"
              value={restTime}
              onChangeText={setRestTime}
              keyboardType="number-pad"
            />
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            <Text style={styles.submitButtonText}>
              {loading ? 'Updating...' : 'Update Set'}
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
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
  },
  closeButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 16,
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
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
  },
  picker: {
    height: 44,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  chip: {
    paddingHorizontal: 18,
    paddingVertical: 11,
    borderRadius: 22,
    marginRight: 10,
    marginBottom: 10,
    minWidth: 85,
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
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
