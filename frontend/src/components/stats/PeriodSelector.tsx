/**
 * Period selector: 7 | 30 | 90 days. Styling consistent with app (e.g. Profile units toggle).
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

export type PeriodValue = 7 | 30 | 90;

const OPTIONS: PeriodValue[] = [7, 30, 90];

interface PeriodSelectorProps {
  value: PeriodValue;
  onChange: (v: PeriodValue) => void;
}

export const PeriodSelector: React.FC<PeriodSelectorProps> = ({ value, onChange }) => {
  return (
    <View style={styles.row}>
      {OPTIONS.map((p) => (
        <TouchableOpacity
          key={p}
          style={[styles.segment, value === p && styles.segmentActive]}
          onPress={() => onChange(p)}
          activeOpacity={0.7}
        >
          <Text style={[styles.segmentText, value === p && styles.segmentTextActive]}>
            {p} Days
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    gap: 8,
  },
  segment: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#e0e0e0',
    alignItems: 'center',
  },
  segmentActive: {
    backgroundColor: '#007AFF',
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  segmentTextActive: {
    color: '#fff',
  },
});
