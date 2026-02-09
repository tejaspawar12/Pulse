/**
 * History Screen - Shows workout history with pagination.
 * Phase 2 Week 3 Day 5: Preview row at top linking to Progress & Trends.
 * Phase 2 Week 4: Offline cache — when offline show cached history and preview; when online fetch and cache.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
  Platform,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { WorkoutSummary } from '../types/workout.types';
import { workoutApi } from '../services/api/workout.api';
import { statsApi } from '../services/api/stats.api';
import type { StatsSummary } from '../services/api/stats.api';
import { WorkoutListItem } from '../components/history/WorkoutListItem';
import { useUserStore } from '../store/userStore';
import { useUserUnit } from '../hooks/useUserUnit';
import { useOfflineCache } from '../hooks/useOfflineCache';
import { useOfflineStore } from '../store/offlineStore';
import { VerifyEmailBanner } from '../components/common/VerifyEmailBanner';
import { OfflineBanner } from '../components/common/OfflineBanner';
import { convertWeightForDisplay, getUnitLabel } from '../utils/units';
import { isPortfolioMode } from '../config/constants';
import { authApi } from '../services/api/auth.api';

const DEMO_EMAIL = 'demo@example.com';

export const HistoryScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const userProfile = useUserStore((s) => s.userProfile);
  const [workouts, setWorkouts] = useState<WorkoutSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewSummary, setPreviewSummary] = useState<StatsSummary | null>(null);
  const [seeding, setSeeding] = useState(false);

  const units = useUserUnit();
  const { isOnline, cachedHistory, getCachedOrFetchStatsSummary7 } = useOfflineCache();

  // ⚠️ FIX: Avoid onEndReached firing on mount
  const didMountRef = useRef(false);
  const hasInitiallyLoadedRef = useRef(false);

  const loadWorkouts = useCallback(
    async (cursor?: string) => {
      try {
        setError(null);

        if (cursor) {
          setLoadingMore(true);
        } else {
          setLoading(true);
        }

        if (!isOnline) {
          if (cursor) {
            setLoadingMore(false);
            return;
          }
          setWorkouts(cachedHistory);
          setNextCursor(null);
          setHasMore(false);
          setLoading(false);
          return;
        }

        const response = await workoutApi.getHistory(cursor, 20);

        if (cursor) {
          setWorkouts((prev) => [...prev, ...response.items]);
        } else {
          setWorkouts(response.items);
          useOfflineStore.getState().setCachedHistory(response.items);
        }

        setNextCursor(response.next_cursor);
        setHasMore(response.next_cursor !== null);
      } catch (err: any) {
        console.error('Error loading workout history:', err);
        if (workouts.length === 0) {
          setError('Failed to load workout history. Please try again.');
        }
        if (!isOnline && cachedHistory.length > 0) {
          setWorkouts(cachedHistory);
          setNextCursor(null);
          setHasMore(false);
        }
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [isOnline, cachedHistory]
  );

  // Load initial workouts
  useEffect(() => {
    loadWorkouts().then(() => {
      hasInitiallyLoadedRef.current = true;
    });
  }, [loadWorkouts]);

  // Refetch when History tab is focused (e.g. after finishing a workout on Log tab)
  useFocusEffect(
    useCallback(() => {
      if (hasInitiallyLoadedRef.current) {
        loadWorkouts();
      }
    }, [loadWorkouts])
  );

  // Fetch last 7 days summary when History tab is focused (for preview row); use cache when offline
  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getCachedOrFetchStatsSummary7(() => statsApi.getSummary(7)).then((data) => {
        if (!cancelled) setPreviewSummary(data ?? null);
      });
      return () => { cancelled = true; };
    }, [getCachedOrFetchStatsSummary7])
  );
  
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadWorkouts();
    setRefreshing(false);
  }, [loadWorkouts]);
  
  const handleLoadMore = useCallback(() => {
    // ⚠️ FIX: Avoid onEndReached firing on mount
    // Only ignore first call if list is still empty (initial load state)
    // This prevents blocking legit pagination in short lists
    if (!didMountRef.current) {
      didMountRef.current = true;
      // If list is empty, ignore (initial load still happening)
      // If list has items, allow it (legit pagination)
      if (workouts.length === 0) {
        return;
      }
    }
    
    // ⚠️ FIX: Prevent duplicate onEndReached calls
    // FlatList can call onEndReached multiple times
    // Guard: don't load more if loading OR refreshing OR loadingMore OR empty list
    if (!loading && !refreshing && !loadingMore && hasMore && nextCursor && workouts.length > 0) {
      loadWorkouts(nextCursor);
    }
  }, [loading, refreshing, loadingMore, hasMore, nextCursor, loadWorkouts, workouts.length]);
  
  const handleWorkoutPress = useCallback((workoutId: string) => {
    navigation.navigate('WorkoutDetail', { workoutId });
  }, [navigation]);
  const handleLoadSampleWorkouts = useCallback(async () => {
    if (!isOnline || seeding) return;
    setSeeding(true);
    setError(null);
    try {
      await authApi.demoSeedMe();
      await loadWorkouts();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Failed to load sample workouts.');
    } finally {
      setSeeding(false);
    }
  }, [isOnline, seeding, loadWorkouts]);


  const handleProgressTrendsPress = useCallback(() => {
    navigation.navigate('ProgressTrends');
  }, [navigation]);

  const handleReportPress = useCallback(() => {
    const parent = navigation.getParent() as any;
    const root = parent?.getParent?.();
    if (root?.navigate) {
      root.navigate('WeeklyReport');
    } else if (parent?.navigate) {
      parent.navigate('WeeklyReport');
    }
  }, [navigation]);

  const previewLabel = (() => {
    if (!previewSummary) return 'Last 7 days: —';
    const vol = convertWeightForDisplay(previewSummary.total_volume_kg, units);
    const volStr = vol != null ? `${vol.toFixed(0)} ${getUnitLabel(units)}` : '—';
    return `Last 7 days: ${previewSummary.total_workouts} workouts • ${volStr}`;
  })();

  const isDemoUser = isPortfolioMode && (userProfile?.email ?? '').toLowerCase() === DEMO_EMAIL;

  const renderListHeader = useCallback(() => {
    const webCursor = Platform.OS === 'web' ? { cursor: 'pointer' as const } : {};
    const isWeb = Platform.OS === 'web';
    return (
    <>
      {isWeb ? (
        <View
          style={[styles.linkRow, webCursor]}
          onClick={handleReportPress}
          role="button"
          tabIndex={0}
          onKeyDown={(e: any) => e.key === 'Enter' && handleReportPress()}
        >
          <Text style={styles.linkRowIcon}>📋</Text>
          <Text style={styles.linkRowLabel}>Weekly Report</Text>
          <Text style={styles.chevron}>›</Text>
        </View>
      ) : (
        <Pressable
          style={({ pressed }) => [styles.linkRow, pressed && { opacity: 0.7 }]}
          onPress={handleReportPress}
        >
          <Text style={styles.linkRowIcon}>📋</Text>
          <Text style={styles.linkRowLabel}>Weekly Report</Text>
          <Text style={styles.chevron}>›</Text>
        </Pressable>
      )}
      {isWeb ? (
        <View
          style={[styles.linkRow, webCursor]}
          onClick={handleProgressTrendsPress}
          role="button"
          tabIndex={0}
          onKeyDown={(e: any) => e.key === 'Enter' && handleProgressTrendsPress()}
        >
          <Text style={styles.linkRowIcon}>📈</Text>
          <Text style={styles.linkRowLabel}>Progress & Trends</Text>
          <Text style={styles.chevron}>›</Text>
        </View>
      ) : (
        <Pressable
          style={({ pressed }) => [styles.linkRow, pressed && { opacity: 0.7 }]}
          onPress={handleProgressTrendsPress}
        >
          <Text style={styles.linkRowIcon}>📈</Text>
          <Text style={styles.linkRowLabel}>Progress & Trends</Text>
          <Text style={styles.chevron}>›</Text>
        </Pressable>
      )}
      {isWeb ? (
        <View
          style={[styles.previewRow, webCursor]}
          onClick={handleProgressTrendsPress}
          role="button"
          tabIndex={0}
          onKeyDown={(e: any) => e.key === 'Enter' && handleProgressTrendsPress()}
        >
          <Text style={styles.previewRowText} numberOfLines={1}>{previewLabel}</Text>
          <Text style={styles.chevron}>›</Text>
        </View>
      ) : (
        <Pressable
          style={({ pressed }) => [styles.previewRow, pressed && { opacity: 0.7 }]}
          onPress={handleProgressTrendsPress}
        >
          <Text style={styles.previewRowText} numberOfLines={1}>{previewLabel}</Text>
          <Text style={styles.chevron}>›</Text>
        </Pressable>
      )}
      {isDemoUser && (
        <TouchableOpacity
          style={[styles.loadSampleButtonHeader, seeding && styles.loadSampleButtonDisabled]}
          onPress={handleLoadSampleWorkouts}
          disabled={seeding || !isOnline}
        >
          {seeding ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.loadSampleButtonText}>
              {workouts.length > 0 ? 'Reload sample workouts' : 'Load sample workouts'}
            </Text>
          )}
        </TouchableOpacity>
      )}
    </>
  );
  }, [previewLabel, handleProgressTrendsPress, handleReportPress, isDemoUser, seeding, isOnline, handleLoadSampleWorkouts, workouts.length]);
  
  const containerStyle = [styles.centerContainer, Platform.OS === 'web' && { minHeight: '100vh' }];

  if (loading && workouts.length === 0) {
    return (
      <View style={containerStyle}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading history...</Text>
      </View>
    );
  }

  if (error && workouts.length === 0) {
    return (
      <View style={containerStyle}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => loadWorkouts()}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  return (
    <View style={[styles.container, Platform.OS === 'web' && { minHeight: '100vh' }]}>
      {!isPortfolioMode && !userProfile?.email_verified && <VerifyEmailBanner />}
      <FlatList
        data={workouts}
        ListHeaderComponent={renderListHeader}
        renderItem={({ item }) => (
          <WorkoutListItem
            workout={item}
            onPress={() => handleWorkoutPress(item.id)}
          />
        )}
        keyExtractor={(item) => String(item.id)}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.2}
        ListFooterComponent={
          loadingMore ? (
            <View style={styles.footer}>
              <ActivityIndicator size="small" />
            </View>
          ) : null
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            {!isOnline ? (
              <>
                <Text style={styles.emptyText}>No cached history</Text>
                <Text style={styles.emptySubtext}>
                  Go online to load your workout history.
                </Text>
              </>
            ) : (
              <>
                <Text style={styles.emptyText}>No workouts yet</Text>
                <Text style={styles.emptySubtext}>
                  {isPortfolioMode
                    ? 'Start a workout from Log, or load sample workouts below.'
                    : 'Start a workout to see it here!'}
                </Text>
                {isDemoUser && (
                  <TouchableOpacity
                    style={[styles.loadSampleButton, seeding && styles.loadSampleButtonDisabled]}
                    onPress={handleLoadSampleWorkouts}
                    disabled={seeding}
                  >
                    {seeding ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.loadSampleButtonText}>Load sample workouts</Text>
                    )}
                  </TouchableOpacity>
                )}
              </>
            )}
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  linkRowIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  linkRowLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  previewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 8,
    marginHorizontal: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  previewRowText: {
    fontSize: 15,
    color: '#333',
    flex: 1,
  },
  chevron: {
    fontSize: 20,
    color: '#999',
    marginLeft: 8,
  },
  loadSampleButton: {
    marginTop: 20,
    backgroundColor: '#34C759',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  loadSampleButtonHeader: {
    marginHorizontal: 16,
    marginBottom: 8,
    backgroundColor: '#34C759',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  loadSampleButtonDisabled: {
    opacity: 0.7,
  },
  loadSampleButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
