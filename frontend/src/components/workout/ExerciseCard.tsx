/**
 * Exercise Card component.
 * Displays exercise name, sets count, and actions.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { WorkoutExercise, WorkoutSet, LastPerformance } from '../../types/workout.types';
import { SetRow } from './SetRow';
import { userApi } from '../../services/api/user.api';
import { useUserStore } from '../../store/userStore';
import { convertWeightForDisplay, getUnitLabel } from '../../utils/units';
import { parseLocalYMD, formatMonthDay } from '../../utils/date';

interface ExerciseCardProps {
  exercise: WorkoutExercise;
  onPress?: () => void;
  onAddSet?: () => void;
  onEditSet?: (set: WorkoutSet) => void;
  onDeleteSet?: (setId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
}

export const ExerciseCard: React.FC<ExerciseCardProps> = ({
  exercise,
  onPress,
  onAddSet,
  onEditSet,
  onDeleteSet,
  onMoveUp,
  onMoveDown,
  canMoveUp = false,
  canMoveDown = false,
}) => {
  const userProfile = useUserStore((state) => state.userProfile);
  const userUnit = userProfile?.units || 'kg';
  const unitLabel = getUnitLabel(userUnit);
  
  const setsCount = exercise.sets.length;
  const [lastPerformance, setLastPerformance] = useState<LastPerformance | null>(null);
  const [loadingPerformance, setLoadingPerformance] = useState(false);
  
  // Sort sets by set_number to ensure correct order
  const sortedSets = [...exercise.sets].sort((a, b) => a.set_number - b.set_number);
  
  // Load previous performance when exercise changes
  useEffect(() => {
    const loadPerformance = async () => {
      if (!exercise.exercise_id) return;
      
      try {
        setLoadingPerformance(true);
        const performance = await userApi.getLastPerformance(exercise.exercise_id);
        setLastPerformance(performance);
      } catch (error) {
        console.error('Error loading previous performance:', error);
        setLastPerformance(null);
      } finally {
        setLoadingPerformance(false);
      }
    };
    
    loadPerformance();
  }, [exercise.exercise_id]);
  
  const formatPerformance = (): string | null => {
    if (!lastPerformance || lastPerformance.sets.length === 0) return null;
    
    const sets = lastPerformance.sets;
    const firstSet = sets[0];
    
    // ⚠️ CRITICAL FIX: Use parseLocalYMD to prevent timezone shift bug
    const date = parseLocalYMD(lastPerformance.last_date);
    const formattedDate = formatMonthDay(date);
    
    // Format: "Last: 3×8×60kg on Jan 15"
    if (firstSet.reps && firstSet.weight) {
      const displayWeight = convertWeightForDisplay(firstSet.weight, userUnit);
      
      if (sets.length === 1) {
        return `Last: ${firstSet.reps}×${displayWeight}${unitLabel} on ${formattedDate}`;
      } else {
        return `Last: ${sets.length}×${firstSet.reps}×${displayWeight}${unitLabel} on ${formattedDate}`;
      }
    } else if (firstSet.reps) {
      return `Last: ${sets.length}×${firstSet.reps} reps on ${formattedDate}`;
    } else if (firstSet.duration_seconds) {
      return `Last: ${sets.length}×${firstSet.duration_seconds}s on ${formattedDate}`;
    }
    
    return null;
  };
  
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            {/* Reorder buttons */}
            {(onMoveUp || onMoveDown) && (
              <View style={styles.reorderButtons}>
                {onMoveUp && (
                  <TouchableOpacity
                    style={[styles.reorderButton, !canMoveUp && styles.reorderButtonDisabled]}
                    onPress={onMoveUp}
                    disabled={!canMoveUp}
                    activeOpacity={0.7}
                  >
                    <Text style={[styles.reorderButtonText, !canMoveUp && styles.reorderButtonTextDisabled]}>↑</Text>
                  </TouchableOpacity>
                )}
                {onMoveDown && (
                  <TouchableOpacity
                    style={[styles.reorderButton, !canMoveDown && styles.reorderButtonDisabled]}
                    onPress={onMoveDown}
                    disabled={!canMoveDown}
                    activeOpacity={0.7}
                  >
                    <Text style={[styles.reorderButtonText, !canMoveDown && styles.reorderButtonTextDisabled]}>↓</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
            
            <TouchableOpacity
              style={styles.headerTextContainer}
              onPress={onPress}
              activeOpacity={0.7}
            >
              <Text style={styles.exerciseName}>{exercise.exercise_name}</Text>
              <Text style={styles.setsCount}>
                {setsCount} {setsCount === 1 ? 'set' : 'sets'}
              </Text>
            </TouchableOpacity>
          </View>
          {onAddSet && (
            <TouchableOpacity
              style={styles.addSetButtonInline}
              onPress={onAddSet}
              activeOpacity={0.7}
            >
              <Text style={styles.addSetButtonInlineText}>+</Text>
            </TouchableOpacity>
          )}
        </View>
        
        {/* Previous Performance */}
        {formatPerformance() && (
          <View style={styles.previousPerformanceContainer}>
            <Text style={styles.previousPerformanceText}>{formatPerformance()}</Text>
          </View>
        )}
        
        {/* Sets list */}
        {setsCount > 0 && (
          <View style={styles.setsContainer}>
            {sortedSets.map((set) => (
              <SetRow
                key={set.id}
                set={set}
                onPress={() => onEditSet?.(set)}
                onDelete={() => onDeleteSet?.(set.id)}
              />
            ))}
            {onAddSet && (
              <TouchableOpacity
                style={styles.addSetButtonBelow}
                onPress={onAddSet}
                activeOpacity={0.7}
              >
                <Text style={styles.addSetButtonBelowText}>+ Add Set</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
        
        {setsCount === 0 && (
          <View style={styles.emptySetsContainer}>
            <Text style={styles.emptySets}>No sets yet</Text>
            {onAddSet && (
              <TouchableOpacity
                style={styles.addSetButtonEmpty}
                onPress={onAddSet}
                activeOpacity={0.7}
              >
                <Text style={styles.addSetButtonEmptyText}>+ Add Set</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
    padding: 0,
    borderWidth: 0,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  headerLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  reorderButtons: {
    flexDirection: 'row',
    marginRight: 8,
  },
  reorderButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    borderRadius: 6,
    marginRight: 4,
  },
  reorderButtonDisabled: {
    opacity: 0.3,
  },
  reorderButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600',
  },
  reorderButtonTextDisabled: {
    color: '#999',
  },
  headerTextContainer: {
    flex: 1,
  },
  exerciseName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4,
  },
  setsCount: {
    fontSize: 13,
    color: '#999',
    fontWeight: '500',
  },
  addSetButtonInline: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 12,
  },
  addSetButtonInlineText: {
    fontSize: 22,
    color: '#fff',
    fontWeight: '300',
    lineHeight: 22,
  },
  emptySetsContainer: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  emptySets: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  addSetButtonEmpty: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BBDEFB',
  },
  addSetButtonEmptyText: {
    fontSize: 15,
    color: '#007AFF',
    fontWeight: '600',
  },
  addSetButtonBelow: {
    marginTop: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BBDEFB',
    alignItems: 'center',
  },
  addSetButtonBelowText: {
    fontSize: 15,
    color: '#007AFF',
    fontWeight: '600',
  },
  setsContainer: {
    marginTop: 8,
  },
  previousPerformanceContainer: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#f9f9f9',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    marginTop: -12,
    marginBottom: 12,
  },
  previousPerformanceText: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
  },
});
