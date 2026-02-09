/**
 * Banner prompting user to verify email (Phase 2 Week 1).
 * Shown on Log/History when user is not verified. Taps navigate to VerifyEmail screen.
 */
import React from 'react';
import { Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';

interface Props {
  onPress?: () => void;
}

export const VerifyEmailBanner: React.FC<Props> = ({ onPress }) => {
  const navigation = useNavigation();

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      (navigation as any).navigate('VerifyEmail');
    }
  };

  return (
    <TouchableOpacity style={styles.container} onPress={handlePress} activeOpacity={0.8}>
      <Text style={styles.text}>
        ✉️ Verify your email to activate your 7-day AI coaching trial
      </Text>
      <Text style={styles.arrow}>→</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FEF3C7',
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  text: {
    flex: 1,
    color: '#92400E',
    fontSize: 14,
  },
  arrow: {
    color: '#92400E',
    fontSize: 18,
    marginLeft: 8,
  },
});
