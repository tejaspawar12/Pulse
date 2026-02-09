/**
 * EditPlanModal: form to edit plan preferences (days/week, session min, split, progression, deload).
 * Uses PATCH /plan/preferences. Valid split: full_body, upper_lower, push_pull_legs. Progression: linear, wave, autoregulated.
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  Alert,
  ScrollView,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import type { Plan, PlanPreferencesUpdate } from '../../services/api/plan.api';

const SPLIT_OPTIONS: { value: string; label: string }[] = [
  { value: 'full_body', label: 'Full body' },
  { value: 'upper_lower', label: 'Upper/Lower' },
  { value: 'push_pull_legs', label: 'Push/Pull/Legs' },
];

const PROGRESSION_OPTIONS: { value: string; label: string }[] = [
  { value: 'linear', label: 'Linear' },
  { value: 'wave', label: 'Wave' },
  { value: 'autoregulated', label: 'Autoregulated' },
];

interface EditPlanModalProps {
  visible: boolean;
  plan: Plan | null;
  onClose: () => void;
  onSave: (body: PlanPreferencesUpdate) => Promise<boolean>;
}

export const EditPlanModal: React.FC<EditPlanModalProps> = ({
  visible,
  plan,
  onClose,
  onSave,
}) => {
  const [daysPerWeek, setDaysPerWeek] = useState('');
  const [sessionMinutes, setSessionMinutes] = useState('');
  const [splitType, setSplitType] = useState<string>('full_body');
  const [progressionType, setProgressionType] = useState<string>('linear');
  const [deloadWeeks, setDeloadWeeks] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (visible && plan) {
      setDaysPerWeek(plan.days_per_week != null ? String(plan.days_per_week) : '');
      setSessionMinutes(plan.session_duration_target != null ? String(plan.session_duration_target) : '');
      setSplitType(plan.split_type || 'full_body');
      setProgressionType(plan.progression_type || 'linear');
      setDeloadWeeks(plan.deload_week_frequency != null ? String(plan.deload_week_frequency) : '');
    }
  }, [visible, plan]);

  const handleSave = async () => {
    const days = daysPerWeek.trim() ? parseInt(daysPerWeek, 10) : undefined;
    const minutes = sessionMinutes.trim() ? parseInt(sessionMinutes, 10) : undefined;
    const deload = deloadWeeks.trim() ? parseInt(deloadWeeks, 10) : undefined;
    if (days !== undefined && (days < 1 || days > 7)) {
      Alert.alert('Invalid value', 'Days per week must be between 1 and 7.');
      return;
    }
    if (minutes !== undefined && (minutes < 15 || minutes > 180)) {
      Alert.alert('Invalid value', 'Session duration must be between 15 and 180 minutes.');
      return;
    }
    if (deload !== undefined && (deload < 1 || deload > 12)) {
      Alert.alert('Invalid value', 'Deload frequency must be between 1 and 12 weeks.');
      return;
    }
    const body: PlanPreferencesUpdate = {};
    if (days !== undefined) body.days_per_week = days;
    if (minutes !== undefined) body.session_duration_target = minutes;
    if (splitType) body.split_type = splitType;
    if (progressionType) body.progression_type = progressionType;
    if (deload !== undefined) body.deload_week_frequency = deload;
    setSaving(true);
    try {
      const ok = await onSave(body);
      if (ok) onClose();
      else Alert.alert('Error', 'Failed to update plan. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (!plan) return null;

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <View style={styles.header}>
            <Text style={styles.title}>Edit plan</Text>
            <TouchableOpacity onPress={onClose} hitSlop={12}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.scroll} keyboardShouldPersistTaps="handled">
            <Text style={styles.fieldLabel}>Days per week (1–7)</Text>
            <TextInput
              style={styles.input}
              value={daysPerWeek}
              onChangeText={setDaysPerWeek}
              keyboardType="number-pad"
              placeholder="e.g. 3"
              placeholderTextColor="#999"
            />
            <Text style={styles.fieldLabel}>Session target (minutes, 15–180)</Text>
            <TextInput
              style={styles.input}
              value={sessionMinutes}
              onChangeText={setSessionMinutes}
              keyboardType="number-pad"
              placeholder="e.g. 45"
              placeholderTextColor="#999"
            />
            <Text style={styles.fieldLabel}>Split</Text>
            <View style={styles.pickerWrap}>
              <Picker
                selectedValue={splitType}
                onValueChange={setSplitType}
                style={styles.picker}
                prompt="Split type"
              >
                {SPLIT_OPTIONS.map((o) => (
                  <Picker.Item key={o.value} label={o.label} value={o.value} />
                ))}
              </Picker>
            </View>
            <Text style={styles.fieldLabel}>Progression</Text>
            <View style={styles.pickerWrap}>
              <Picker
                selectedValue={progressionType}
                onValueChange={setProgressionType}
                style={styles.picker}
                prompt="Progression type"
              >
                {PROGRESSION_OPTIONS.map((o) => (
                  <Picker.Item key={o.value} label={o.label} value={o.value} />
                ))}
              </Picker>
            </View>
            <Text style={styles.fieldLabel}>Deload every (weeks, 1–12)</Text>
            <TextInput
              style={styles.input}
              value={deloadWeeks}
              onChangeText={setDeloadWeeks}
              keyboardType="number-pad"
              placeholder="e.g. 4"
              placeholderTextColor="#999"
            />
          </ScrollView>
          <TouchableOpacity
            style={[styles.saveButton, saving && styles.saveButtonDisabled]}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>Save</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    maxHeight: '85%',
    paddingBottom: Platform.OS === 'ios' ? 28 : 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
  },
  cancelText: {
    fontSize: 16,
    color: '#007AFF',
  },
  scroll: {
    paddingHorizontal: 16,
    paddingTop: 16,
    maxHeight: 360,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#111',
  },
  pickerWrap: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    ...(Platform.OS === 'android' && { height: 48 }),
  },
  picker: {
    ...(Platform.OS === 'ios' && { height: 120 }),
  },
  saveButton: {
    marginHorizontal: 16,
    marginTop: 20,
    backgroundColor: '#007AFF',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
