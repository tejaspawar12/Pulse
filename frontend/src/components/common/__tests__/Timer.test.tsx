/**
 * Tests for Timer component.
 */
import React from 'react';
import { render } from '@testing-library/react-native';
import { Timer } from '../Timer';

describe('Timer', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('displays correct elapsed time in MM:SS format', () => {
    // Freeze time at specific moment
    const fixedTime = new Date('2026-01-24T10:00:00Z');
    jest.setSystemTime(fixedTime);
    
    // Start time is 2 minutes 5 seconds ago
    const startTime = new Date('2026-01-24T09:57:55Z');
    
    const { getByText } = render(<Timer startTime={startTime.toISOString()} />);
    
    expect(getByText(/02:05/)).toBeTruthy();
  });

  it('displays correct elapsed time in HH:MM:SS format for long workouts', () => {
    const fixedTime = new Date('2026-01-24T11:01:05Z');
    jest.setSystemTime(fixedTime);
    
    // Start time is 1 hour 1 minute 5 seconds ago
    const startTime = new Date('2026-01-24T10:00:00Z');
    
    const { getByText } = render(<Timer startTime={startTime.toISOString()} />);
    
    expect(getByText(/01:01:05/)).toBeTruthy();
  });

  it('handles invalid startTime gracefully', () => {
    // Should not crash and render something (could be 00:00, --:--, Invalid, etc.)
    expect(() => render(<Timer startTime="invalid" />)).not.toThrow();
    
    // If your Timer shows specific fallback, assert that:
    // const { getByText } = render(<Timer startTime="invalid" />);
    // expect(getByText(/00:00|--:--|Invalid/)).toBeTruthy();
    
    // Or just verify it renders without crashing:
    const { container } = render(<Timer startTime="invalid" />);
    expect(container).toBeTruthy();
  });
});
