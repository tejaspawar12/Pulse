/**
 * Banner shown when offline. Phase 2 Week 4.
 * "You're offline. Viewing cached data."
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useOfflineCache } from '../../hooks/useOfflineCache';

export const OfflineBanner: React.FC = () => {
  const { isOnline, lastCacheUpdate } = useOfflineCache();

  if (isOnline) return null;

  const historyTs = lastCacheUpdate.history;
  const cachedHint = historyTs
    ? `Cached • updated ${formatTimeAgo(historyTs)}`
    : 'Cached data';

  return (
    <View style={styles.banner}>
      <Text style={styles.text}>You're offline. Viewing cached data.</Text>
      <Text style={styles.hint}>{cachedHint}</Text>
    </View>
  );
};

function formatTimeAgo(ts: number): string {
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return 'just now';
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  return `${Math.floor(sec / 86400)}d ago`;
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#E8790A',
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  text: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  hint: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 12,
    marginTop: 2,
  },
});
