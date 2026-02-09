/**
 * GoalLabel: shows "Your goal: X" with optional link to Profile to change it.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useOfflineCache } from '../../hooks/useOfflineCache';
import { useCoachProfile } from '../../hooks/useCoachProfile';

export const GoalLabel: React.FC = () => {
  const { isOnline } = useOfflineCache();
  const { goalLabel, loading } = useCoachProfile(isOnline);
  const navigation = useNavigation<any>();

  if (loading) return null;

  const handlePress = () => {
    const tabNav = navigation.getParent?.();
    if (tabNav?.navigate) {
      tabNav.navigate('Profile');
    }
  };

  return (
    <TouchableOpacity onPress={handlePress} activeOpacity={0.7} style={styles.wrapper}>
      <View style={styles.row}>
        <Text style={styles.prefix}>Your goal:</Text>
        <Text style={styles.value} numberOfLines={1}>
          {goalLabel || 'Not set'}
        </Text>
        <Text style={styles.hint}>Tap to change in Profile</Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#f0f4ff',
    borderRadius: 8,
    marginHorizontal: 16,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 4,
  },
  prefix: {
    fontSize: 13,
    color: '#666',
  },
  value: {
    fontSize: 13,
    fontWeight: '600',
    color: '#007AFF',
  },
  hint: {
    fontSize: 11,
    color: '#999',
    marginLeft: 4,
  },
});
