/**
 * Tests for ExerciseCard component.
 */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ExerciseCard } from '../ExerciseCard';
import { WorkoutExercise, SetType } from '../../../types/workout.types';

// Mock userApi to prevent API calls in useEffect
jest.mock('../../../services/api/user.api', () => ({
  userApi: {
    getLastPerformance: jest.fn().mockResolvedValue(null),
  },
}));

// Mock userStore
jest.mock('../../../store/userStore', () => ({
  useUserStore: jest.fn(() => ({
    userProfile: { units: 'kg' },
  })),
}));

describe('ExerciseCard', () => {
  const mockExercise: WorkoutExercise = {
    id: 'exercise-1',
    exercise_id: 'lib-1',
    exercise_name: 'Bench Press',
    order_index: 0,
    sets: [],
    created_at: new Date().toISOString(),
  };

  it('displays exercise name and sets count', () => {
    const { getByText } = render(<ExerciseCard exercise={mockExercise} />);
    
    expect(getByText('Bench Press')).toBeTruthy();
    expect(getByText('0 sets')).toBeTruthy();
  });

  it('calls onAddSet when add button clicked', () => {
    const onAddSet = jest.fn();
    const { getByText } = render(
      <ExerciseCard exercise={mockExercise} onAddSet={onAddSet} />
    );
    
    fireEvent.press(getByText('+'));
    expect(onAddSet).toHaveBeenCalledTimes(1);
  });

  it('displays sets when present', () => {
    const exerciseWithSets: WorkoutExercise = {
      ...mockExercise,
      sets: [
        {
          id: 'set-1',
          set_number: 0,
          reps: 8,
          weight: 60,
          set_type: SetType.WORKING,
          created_at: new Date().toISOString(),
        },
      ],
    };
    
    const { getByText } = render(<ExerciseCard exercise={exerciseWithSets} />);
    
    expect(getByText('8')).toBeTruthy();
    expect(getByText('60')).toBeTruthy();
  });
});
