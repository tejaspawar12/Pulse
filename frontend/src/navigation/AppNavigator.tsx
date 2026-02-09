/**
 * Main app navigator with bottom tabs.
 * Includes Active Workout Bar on all tabs when workout is active.
 * Handles authentication flow (login/register vs app).
 */
import React, { useEffect } from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { LogScreen } from '../screens/LogScreen';
import { HistoryStackNavigator } from './HistoryStackNavigator';
import { CoachScreen } from '../screens/CoachScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { WeeklyReportScreen } from '../screens/WeeklyReportScreen';
import { TimelineDetailsScreen } from '../screens/TimelineDetailsScreen';
import { PlanDetailsScreen } from '../screens/PlanDetailsScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { VerifyEmailScreen } from '../screens/VerifyEmailScreen';
import { ActiveWorkoutSummary } from '../types/workout.types';
import { useUserStore } from '../store/userStore';
import { isPortfolioMode } from '../config/constants';
import type { AuthStackParamList, MainStackParamList, TabParamList } from './types';

const Tab = createBottomTabNavigator<TabParamList>();
const AuthStack = createStackNavigator<AuthStackParamList>();
const MainStack = createStackNavigator<MainStackParamList>();

interface AppNavigatorProps {
  activeWorkoutSummary: ActiveWorkoutSummary | null; // Passed from App.tsx to avoid Zustand access
}

const AppNavigatorComponent: React.FC<AppNavigatorProps> = ({ activeWorkoutSummary }) => {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const authLoading = useUserStore((state) => state.authLoading);
  const initAuth = useUserStore((state) => state.initAuth);

  // Initialize auth on mount
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // ⚠️ CRITICAL: Show loading screen during auth bootstrap to prevent login flash
  // Without this, users briefly see login screen before auto-login completes
  if (authLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  // Show auth screens if not authenticated
  if (!isAuthenticated) {
    return (
      <AuthStack.Navigator
        screenOptions={{
          headerShown: false,
        }}
      >
        <AuthStack.Screen name="Login" component={LoginScreen} />
        {!isPortfolioMode && (
          <AuthStack.Screen name="Register" component={RegisterScreen} />
        )}
      </AuthStack.Navigator>
    );
  }

  // Show main app: stack with tabs + VerifyEmail screen (Phase 2 Week 1)
  // Hevy-like: hide tab bar when workout is active so screen is focused on logging
  const isWeb = Platform.OS === 'web';
  const MainTabsScreen = () => (
    <View style={styles.tabsContainer}>
      <Tab.Navigator
        screenOptions={{
          headerShown: true,
          tabBarLabelStyle: isWeb ? styles.tabBarLabelWeb : { fontSize: 12 },
          tabBarItemStyle: isWeb ? styles.tabBarItemWeb : undefined,
          tabBarStyle: [
            { display: activeWorkoutSummary ? 'none' : 'flex' },
            isWeb && styles.tabBarWeb,
          ].filter(Boolean),
        }}
      >
        <Tab.Screen
          name="Log"
          component={LogScreen}
          options={{
            title: 'Log Workout',
            tabBarLabel: 'Log',
            tabBarIcon: () => <Text>🏋️</Text>,
          }}
        />
        <Tab.Screen
          name="History"
          component={HistoryStackNavigator}
          options={{
            title: 'History',
            tabBarLabel: 'History',
            tabBarIcon: () => <Text>📜</Text>,
            headerShown: false,
          }}
        />
        <Tab.Screen
          name="Coach"
          component={CoachScreen}
          options={{
            title: 'Coach',
            tabBarLabel: 'Coach',
            tabBarIcon: () => <Text>💬</Text>,
          }}
        />
        <Tab.Screen
          name="Profile"
          component={ProfileScreen}
          options={{
            title: 'Profile',
            tabBarLabel: 'Profile',
            tabBarIcon: () => <Text>👤</Text>,
          }}
        />
      </Tab.Navigator>
      {/* No ActiveWorkoutBar when workout is active: tabs are hidden and timer is in Log stats row */}
    </View>
  );

  return (
    <MainStack.Navigator screenOptions={{ headerShown: true }}>
      <MainStack.Screen
        name="MainTabs"
        component={MainTabsScreen}
        options={{ headerShown: false }}
      />
      <MainStack.Screen
        name="VerifyEmail"
        component={VerifyEmailScreen}
        options={{ title: 'Verify Email' }}
      />
      <MainStack.Screen
        name="WeeklyReport"
        component={WeeklyReportScreen}
        options={{ title: 'Weekly Report' }}
      />
      <MainStack.Screen
        name="TimelineDetails"
        component={TimelineDetailsScreen}
        options={{ title: 'Transformation Timeline' }}
      />
      <MainStack.Screen
        name="PlanDetails"
        component={PlanDetailsScreen}
        options={{ title: 'Your Training Plan' }}
      />
    </MainStack.Navigator>
  );
};

const styles = StyleSheet.create({
  tabsContainer: {
    flex: 1,
  },
  // Web: taller bar so labels are fully visible; extra padding above browser chrome on mobile
  tabBarWeb: {
    minHeight: 64,
    paddingTop: 8,
    paddingBottom: 12,
  },
  // Web: larger label so "Log", "History", "Coach", "Profile" are fully visible on mobile
  tabBarLabelWeb: {
    fontSize: 13,
    fontWeight: '500',
  },
  // Web: bigger touch targets and equal width so tabs are easy to tap on mobile
  tabBarItemWeb: {
    flex: 1,
    minHeight: 48,
    paddingVertical: 6,
    paddingHorizontal: 4,
    cursor: 'pointer',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
});

// Memoize to prevent unnecessary re-renders
// Only re-render when activeWorkoutSummary prop changes
export const AppNavigator = React.memo(AppNavigatorComponent, (prevProps, nextProps) => {
  // Only re-render if activeWorkoutSummary actually changed
  return prevProps.activeWorkoutSummary === nextProps.activeWorkoutSummary;
});
