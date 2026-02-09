/**
 * Exercise Picker modal component.
 * Allows users to search and select exercises to add to workout.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Exercise } from '../../types/exercise.types';
import { exerciseApi, ExerciseSearchParams } from '../../services/api/exercise.api';
import { ExerciseItem } from './ExerciseItem';

interface ExercisePickerProps {
  visible: boolean;
  onClose: () => void;
  onSelect: (exercise: Exercise) => void;
}

// Muscle groups and equipment for filter chips
const MUSCLE_GROUPS = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core'];
const EQUIPMENT_TYPES = ['barbell', 'dumbbell', 'machine', 'bodyweight', 'cable'];

// Debounce utility
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export const ExercisePicker: React.FC<ExercisePickerProps> = ({
  visible,
  onClose,
  onSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMuscleGroup, setSelectedMuscleGroup] = useState<string | null>(null);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [recentExercises, setRecentExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const insets = useSafeAreaInsets();

  // Debounce search query (300ms)
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Load recent exercises on mount
  useEffect(() => {
    if (visible) {
      loadRecentExercises();
    }
  }, [visible]);

  // Search exercises when debounced query or filters change
  useEffect(() => {
    if (!visible) return;

    if (debouncedQuery && debouncedQuery.length >= 2) {
      // Search with query
      searchExercises();
    } else if ((!debouncedQuery || debouncedQuery.length < 2) && !selectedMuscleGroup && !selectedEquipment) {
      // No search query and no filters - show recent
      loadRecentExercises();
      setExercises([]);
    } else if ((!debouncedQuery || debouncedQuery.length < 2) && (selectedMuscleGroup || selectedEquipment)) {
      // Filters but no query - search with filters only
      searchExercises();
    }
  }, [debouncedQuery, selectedMuscleGroup, selectedEquipment, visible]);

  const loadRecentExercises = async () => {
    try {
      setLoading(true);
      setError(null);
      const recent = await exerciseApi.getRecent(10);
      setRecentExercises(recent);
    } catch (err) {
      console.error('Error loading recent exercises:', err);
      setError('Failed to load recent exercises');
    } finally {
      setLoading(false);
    }
  };

  const searchExercises = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: ExerciseSearchParams = {
        q: debouncedQuery && debouncedQuery.length >= 2 ? debouncedQuery : undefined,
        muscle_group: selectedMuscleGroup || undefined,
        equipment: selectedEquipment || undefined,
        limit: 50,
      };

      const results = await exerciseApi.search(params);
      setExercises(results);
    } catch (err) {
      console.error('Error searching exercises:', err);
      setError('Failed to search exercises');
      setExercises([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectExercise = (exercise: Exercise) => {
    onSelect(exercise);
    // Reset state on close
    setSearchQuery('');
    setSelectedMuscleGroup(null);
    setSelectedEquipment(null);
    setExercises([]);
    setError(null);
  };

  const toggleMuscleGroup = (group: string) => {
    setSelectedMuscleGroup(selectedMuscleGroup === group ? null : group);
  };

  const toggleEquipment = (equipment: string) => {
    setSelectedEquipment(selectedEquipment === equipment ? null : equipment);
  };

  const renderFilterChip = (
    label: string,
    isSelected: boolean,
    onPress: () => void
  ) => (
    <TouchableOpacity
      style={[styles.chip, isSelected && styles.chipSelected]}
      onPress={onPress}
    >
      <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  const renderExerciseItem = ({ item }: { item: Exercise }) => (
    <ExerciseItem exercise={item} onPress={handleSelectExercise} />
  );

  // Show recent exercises if no search query (or query < 2 chars) and no filters
  const showRecent = (!debouncedQuery || debouncedQuery.length < 2) && !selectedMuscleGroup && !selectedEquipment;
  const displayExercises = showRecent ? recentExercises : exercises;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <KeyboardAvoidingView
        style={[styles.container, { paddingTop: insets.top }]}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Select Exercise</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>Close</Text>
          </TouchableOpacity>
        </View>

        {/* Search Input - compact */}
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search (min 2 chars)..."
            placeholderTextColor="#999"
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="search"
          />
        </View>

        {/* Filter Chips - compact */}
        <View style={styles.filtersContainer}>
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Muscle</Text>
            <View style={styles.chipsRow}>
              {MUSCLE_GROUPS.map((group) => (
                <React.Fragment key={group}>
                  {renderFilterChip(
                    group,
                    selectedMuscleGroup === group,
                    () => toggleMuscleGroup(group)
                  )}
                </React.Fragment>
              ))}
            </View>
          </View>
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Equipment</Text>
            <View style={styles.chipsRow}>
              {EQUIPMENT_TYPES.map((equip) => (
                <React.Fragment key={equip}>
                  {renderFilterChip(
                    equip,
                    selectedEquipment === equip,
                    () => toggleEquipment(equip)
                  )}
                </React.Fragment>
              ))}
            </View>
          </View>
        </View>

        {/* Content - list dismisses keyboard on scroll */}
        <View style={styles.content}>
          {loading && displayExercises.length === 0 && (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" />
              <Text style={styles.loadingText}>Loading...</Text>
            </View>
          )}

          {error && (
            <View style={styles.centerContainer}>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={showRecent ? loadRecentExercises : searchExercises}
              >
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          )}

          {!loading && !error && displayExercises.length === 0 && (
            <View style={styles.centerContainer}>
              <Text style={styles.emptyText}>
                {showRecent
                  ? 'No recent exercises. Complete a workout to see them here.'
                  : 'No exercises found. Try a different search.'}
              </Text>
            </View>
          )}

          {!loading && !error && displayExercises.length > 0 && (
            <>
              {showRecent && (
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>Recent Exercises</Text>
                </View>
              )}
              <FlatList
                data={displayExercises}
                renderItem={renderExerciseItem}
                keyExtractor={(item) => item.id}
                style={styles.exerciseList}
                contentContainerStyle={styles.exerciseListContent}
                keyboardDismissMode="on-drag"
                keyboardShouldPersistTaps="handled"
              />
            </>
          )}
        </View>
      </KeyboardAvoidingView>
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  closeButton: {
    padding: 8,
  },
  closeButtonText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  searchContainer: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchInput: {
    height: 40,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 15,
    backgroundColor: '#f9f9f9',
  },
  filtersContainer: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  filterSection: {
    marginBottom: 8,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    backgroundColor: '#f0f0f0',
    marginRight: 6,
    marginBottom: 6,
  },
  chipSelected: {
    backgroundColor: '#007AFF',
  },
  chipText: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
  sectionHeader: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#f9f9f9',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  exerciseList: {
    flex: 1,
  },
  exerciseListContent: {
    paddingBottom: 20,
  },
});
