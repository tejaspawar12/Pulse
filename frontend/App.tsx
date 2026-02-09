/**
 * Main App component.
 */
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppNavigator } from './src/navigation/AppNavigator';
import { userApi } from './src/services/api/user.api';
import { ActiveWorkoutSummary } from './src/types/workout.types';
import { View, Text, StyleSheet, ActivityIndicator, InteractionManager } from 'react-native';

// CRITICAL FIX: Don't import store module at top level
// React Navigation serializes modules imported at top level during initial mount
// We'll require it only inside useEffect after NavigationContainer is ready

export default function App() {
  // CRITICAL FIX: NO Zustand hooks or subscriptions - React Navigation serializes store
  // Use local state only, access store ONLY via getState() in useEffect, never subscribe
  const [devUserId, setDevUserIdLocal] = React.useState<string | null>(null);
  const [initializing, setInitializing] = React.useState(true);
  const [activeWorkoutSummary, setActiveWorkoutSummary] = React.useState<ActiveWorkoutSummary | null>(null);
  
  // Store functions in ref - initialized once in useEffect, never accessed during render
  const storeFunctionsRef = React.useRef<{
    setDevUserId: ((userId: string) => Promise<void>) | null;
    setUserStatus: ((status: any) => void) | null;
  }>({ setDevUserId: null, setUserStatus: null });
  
  // Initialize store functions ONCE - no hooks, no subscriptions
  // CRITICAL: Require store module ONLY inside useEffect, not at top level
  // React Navigation serializes top-level imports during initial mount
  React.useEffect(() => {
    // Use setTimeout to ensure this runs after NavigationContainer mounts
    setTimeout(() => {
      try {
        const userStoreModule = require('./src/store/userStore');
        if (userStoreModule && userStoreModule.useUserStore) {
          const store = userStoreModule.useUserStore.getState();
          storeFunctionsRef.current.setDevUserId = store.setDevUserId;
          storeFunctionsRef.current.setUserStatus = store.setUserStatus;
          setDevUserIdLocal(store.devUserId);
          // Only read active_workout, not the full userStatus (which has boolean arrays)
          setActiveWorkoutSummary(store.userStatus?.active_workout || null);
        }
      } catch (e) {
        console.error('Failed to load userStore:', e);
      }
    }, 0);
  }, []);

  // Track if NavigationContainer is ready (prevents Zustand serialization during mount)
  const navigationReadyRef = React.useRef(false);
  const [navigationReady, setNavigationReady] = React.useState(false);
  
  // Subscribe to userStatus changes to update activeWorkoutSummary immediately
  // This ensures ActiveWorkoutBar appears right after starting a workout
  React.useEffect(() => {
    // Only subscribe after NavigationContainer is ready
    if (!navigationReady) return;
    
    let unsubscribe: (() => void) | null = null;
    let timeoutId: NodeJS.Timeout | null = null;
    
    // Use setTimeout to ensure this runs after initial mount
    timeoutId = setTimeout(() => {
      try {
        const userStoreModule = require('./src/store/userStore');
        if (userStoreModule && userStoreModule.useUserStore) {
          const store = userStoreModule.useUserStore;
          let previousUserStatus = store.getState().userStatus;
          
          // Subscribe to all state changes and check if userStatus changed
          unsubscribe = store.subscribe((state) => {
            const currentUserStatus = state.userStatus;
            
            // Only update if userStatus actually changed
            if (currentUserStatus !== previousUserStatus) {
              previousUserStatus = currentUserStatus;
              const activeWorkout = currentUserStatus?.active_workout || null;
              setActiveWorkoutSummary(activeWorkout);
            }
          });
        }
      } catch (e) {
        console.error('Failed to subscribe to userStore:', e);
      }
    }, 100); // Small delay to ensure NavigationContainer is ready
    
    // Cleanup function
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (unsubscribe) unsubscribe();
    };
  }, [navigationReady]); // Re-run when navigation becomes ready
  
  // Load user profile on app start
  React.useEffect(() => {
    const loadUserProfile = async () => {
      try {
        const userStoreModule = require('./src/store/userStore');
        if (userStoreModule && userStoreModule.useUserStore) {
          const profile = await userApi.getProfile();
          userStoreModule.useUserStore.getState().setUserProfile(profile);
        }
      } catch (error) {
        console.error('Failed to load user profile:', error);
        // Use default 'kg' if profile load fails
      }
    };
    
    loadUserProfile();
  }, []);

  // Initialize app: dev user ID + user status
  React.useEffect(() => {
    const bootstrap = async () => {
      try {
        // 1. Initialize dev user ID if not set
        const existingUserId = await AsyncStorage.getItem('dev_user_id');
        
        // CRITICAL: Require store module here (not at top level) to avoid React Navigation serialization
        let userStoreModule: any = null;
        try {
          userStoreModule = require('./src/store/userStore');
          if (userStoreModule && userStoreModule.useUserStore) {
            const store = userStoreModule.useUserStore.getState();
            storeFunctionsRef.current.setDevUserId = store.setDevUserId;
            storeFunctionsRef.current.setUserStatus = store.setUserStatus;
          }
        } catch (e) {
          console.error('Failed to load userStore in bootstrap:', e);
        }
        
        if (!existingUserId) {
          // Set test user ID (get from backend: run create_test_user.py first)
          const TEST_USER_ID = '6b02afa2-2fe6-4140-9745-851c4bc0613f'; // Replace with actual ID
          if (storeFunctionsRef.current.setDevUserId) {
            await storeFunctionsRef.current.setDevUserId(TEST_USER_ID);
            setDevUserIdLocal(TEST_USER_ID);
          }
        } else {
          // Load existing dev user ID into store
          if (storeFunctionsRef.current.setDevUserId) {
            await storeFunctionsRef.current.setDevUserId(existingUserId);
            setDevUserIdLocal(existingUserId);
          }
        }

        // 2. Load user status (includes active_workout summary)
        // CRITICAL FIX: Use setTimeout to ensure API call happens in separate event loop
        // React Navigation serializes objects in scope during render - we must process status completely outside render cycle
        setTimeout(async () => {
          try {
            const status = await userApi.getStatus();
            
            // CRITICAL: Extract active_workout IMMEDIATELY in completely separate scope
            // Status object is now in setTimeout closure, not in React render scope
            const activeWorkout = status?.active_workout || null;
            
            // Update local state with extracted value only (status object not in scope here)
            setActiveWorkoutSummary(activeWorkout);
            
            // CRITICAL: Update Zustand AFTER all interactions complete
            // Require store module here (not at top level) to avoid React Navigation serialization
            InteractionManager.runAfterInteractions(() => {
              try {
                const userStoreModule = require('./src/store/userStore');
                if (userStoreModule && userStoreModule.useUserStore && storeFunctionsRef.current.setUserStatus) {
                  storeFunctionsRef.current.setUserStatus(status);
                }
              } catch (e) {
                console.error('Failed to update Zustand:', e);
              }
            });
          } catch (apiError) {
            console.error('Error loading user status:', apiError);
            setActiveWorkoutSummary(null);
          }
        }, 0);
        
      } catch (error) {
        // userApi.getStatus() handles errors internally, so this catch is unlikely
        // But if it does execute, set safe default with proper booleans
        console.error('Error initializing app:', error);
        const safeDefault = {
          active_workout: null,
          today_worked_out: false, // ✅ boolean, NOT "false" string
          last_30_days: [],
        };
        setActiveWorkoutSummary(null);
        const updateZustand = () => {
          if (storeFunctionsRef.current.setUserStatus && navigationReadyRef.current) {
            InteractionManager.runAfterInteractions(() => {
              if (storeFunctionsRef.current.setUserStatus) {
                storeFunctionsRef.current.setUserStatus(safeDefault);
              }
            });
          } else if (!navigationReadyRef.current) {
            setTimeout(updateZustand, 50);
          }
        };
        updateZustand();
      } finally {
        setInitializing(false);
      }
    };

    bootstrap();
  }, []);

  if (initializing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Initializing...</Text>
      </View>
    );
  }

  if (!devUserId) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Dev User ID not set</Text>
        <Text style={styles.errorSubtext}>
          Please set dev_user_id in AsyncStorage or configure test user
        </Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      {/* SafeAreaProvider must be top-most wrapper for useSafeAreaInsets() to work in ActiveWorkoutBar */}
      <NavigationContainer
        onReady={() => {
          // Mark NavigationContainer as ready - safe to update Zustand now
          navigationReadyRef.current = true;
          setNavigationReady(true);
        }}
      >
        <AppNavigator activeWorkoutSummary={activeWorkoutSummary} />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#d32f2f',
    marginBottom: 10,
  },
  errorSubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
});
