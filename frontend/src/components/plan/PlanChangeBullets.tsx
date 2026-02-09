/**
 * PlanChangeBullets: list of explanation_bullets for an adjustment (Phase 2 Week 7).
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface PlanChangeBulletsProps {
  bullets: string[] | null;
}

export const PlanChangeBullets: React.FC<PlanChangeBulletsProps> = ({ bullets }) => {
  if (!bullets?.length) return null;

  return (
    <View style={styles.container}>
      {bullets.map((b, i) => (
        <View key={i} style={styles.bulletRow}>
          <Text style={styles.bullet}>•</Text>
          <Text style={styles.text}>{b}</Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  bullet: {
    fontSize: 14,
    color: '#007AFF',
    marginRight: 8,
    fontWeight: '600',
  },
  text: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
});
