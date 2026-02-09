/**
 * Profile Screen - User settings and profile.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import { useUserStore } from '../store/userStore';
import { userApi } from '../services/api/user.api';
import { coachApi, type PrimaryGoalValue } from '../services/api/coach.api';
import { pushApi } from '../services/api/push.api';
import { usePushNotifications } from '../hooks/usePushNotifications';
import { getCalendars } from 'expo-localization';
import type { MainStackParamList } from '../navigation/types';
import Constants from 'expo-constants';
const API_URL = typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL
  ? process.env.EXPO_PUBLIC_API_URL
  : 'http://localhost:8000/api/v1';
const APP_VERSION = Constants.expoConfig?.version ?? '1.0.0';
const DEMO_EMAIL = 'demo@example.com';

type ProfileNav = StackNavigationProp<MainStackParamList>;

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<ProfileNav>();
  const userProfile = useUserStore((state) => state.userProfile);
  const setUserProfile = useUserStore((state) => state.setUserProfile);
  const logout = useUserStore((state) => state.logout);
  const [units, setUnits] = useState<'kg' | 'lb'>('kg');
  const [timezone, setTimezone] = useState('');
  const [restTimerText, setRestTimerText] = useState('90'); // ✅ String state for better UX
  const [loading, setLoading] = useState(false);
  const [updatingUnits, setUpdatingUnits] = useState(false);
  const [updatingTimezone, setUpdatingTimezone] = useState(false);
  const [updatingRestTimer, setUpdatingRestTimer] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [reminderTime, setReminderTime] = useState<string | null>(null);
  const [updatingNotifications, setUpdatingNotifications] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [weightKg, setWeightKg] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState<string | null>(null);
  const [updatingBody, setUpdatingBody] = useState(false);
  const [primaryGoal, setPrimaryGoal] = useState<PrimaryGoalValue | null>(null);
  const [updatingGoal, setUpdatingGoal] = useState(false);

  const { registerForPushNotifications } = usePushNotifications();

  // ✅ Use refs for debounce timer and save guard (better than state, avoids typing issues and race conditions)
  const restTimerDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savingRestTimerRef = useRef(false); // ✅ Guard against double-save (ref prevents race conditions)

  // ✅ Load profile on mount (single responsibility)
  useEffect(() => {
    loadProfile();
  }, []);

  // ✅ Initialize state from userProfile when it loads (separate effect)
  useEffect(() => {
    if (!userProfile) return;
    setUnits((userProfile.units as 'kg' | 'lb') ?? 'kg');
    setTimezone(userProfile.timezone ?? '');
    setRestTimerText(String(userProfile.default_rest_timer_seconds ?? 90));
    setNotificationsEnabled(userProfile.notifications_enabled ?? true);
    setReminderTime(userProfile.reminder_time ?? null);
    setWeightKg(userProfile.weight_kg != null ? String(userProfile.weight_kg) : '');
    setHeightCm(userProfile.height_cm != null ? String(userProfile.height_cm) : '');
    setDateOfBirth(userProfile.date_of_birth ?? '');
    setGender(userProfile.gender ?? null);
  }, [userProfile]);

  // Phase 2 Week 2: Register push token when user has notifications enabled
  useEffect(() => {
    if (userProfile?.notifications_enabled !== false) {
      registerForPushNotifications();
    }
  }, [userProfile?.notifications_enabled]);

  // ✅ Cleanup debounce timer on unmount (prevents memory leaks and double-saves)
  useEffect(() => {
    return () => {
      if (restTimerDebounceRef.current) {
        clearTimeout(restTimerDebounceRef.current);
      }
    };
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const [userData, coachData] = await Promise.all([
        userApi.getProfile(),
        coachApi.getProfile().catch(() => null),
      ]);
      setUserProfile(userData);
      if (coachData?.primary_goal) {
        setPrimaryGoal(coachData.primary_goal as PrimaryGoalValue);
      } else {
        setPrimaryGoal(null);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  // ✅ Immediate persistence: Units toggle saves immediately
  const handleUnitsChange = async (newUnits: 'kg' | 'lb') => {
    // ✅ Guard: Don't call PATCH if user taps the already-selected unit
    if (newUnits === units) return;
    
    // ✅ Capture previous value before changing (prevents stale revert)
    const prevUnits = units;
    setUnits(newUnits);
    try {
      setUpdatingUnits(true);
      const updated = await userApi.updateSettings({ units: newUnits });
      setUserProfile(updated);
    } catch (error: any) {
      // Revert to captured previous value (not stale userProfile)
      setUnits(prevUnits);
      const errorMessage = error.response?.data?.detail || 'Failed to update units';
      Alert.alert('Error', errorMessage);
    } finally {
      setUpdatingUnits(false);
    }
  };

  // ✅ Immediate persistence: Timezone saves immediately (from device or picker)
  const handleTimezoneChange = async (newTimezone: string) => {
    // ✅ Guard: Don't call PATCH if timezone hasn't changed
    if (newTimezone === timezone) return;
    
    // ✅ Capture previous value before changing (prevents stale revert)
    const prevTimezone = timezone;
    setTimezone(newTimezone);
    try {
      setUpdatingTimezone(true);
      const updated = await userApi.updateSettings({ timezone: newTimezone });
      setUserProfile(updated);
    } catch (error: any) {
      // Revert to captured previous value (not stale userProfile)
      setTimezone(prevTimezone);
      const errorMessage = error.response?.data?.detail || 'Failed to update timezone';
      Alert.alert('Error', errorMessage);
    } finally {
      setUpdatingTimezone(false);
    }
  };

  // ✅ Detect timezone from device (use getCalendars() - Localization.timezone is deprecated/unavailable)
  const handleDetectTimezone = async () => {
    try {
      const calendars = getCalendars();
      const deviceTimezone = calendars[0]?.timeZone ?? null;
      if (deviceTimezone) {
        await handleTimezoneChange(deviceTimezone);
      } else {
        Alert.alert(
          'Timezone not available',
          'Could not detect your device timezone. It may not be supported on this device or platform.'
        );
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail ?? error?.message ?? 'Failed to detect or save timezone';
      Alert.alert('Error', message);
    }
  };

  // ✅ Rest timer: Update local state while typing, save on blur (debounced)
  // ✅ Use separate function to save (prevents double-save race conditions)
  const saveRestTimer = async (value: number) => {
    // ✅ Guard against double-save using ref (prevents race conditions - ref updates are synchronous)
    if (savingRestTimerRef.current) return;
    savingRestTimerRef.current = true;
    
    try {
      setUpdatingRestTimer(true);
      const updated = await userApi.updateSettings({
        default_rest_timer_seconds: value,
      });
      setUserProfile(updated);
    } catch (error: any) {
      // Revert on error (use current text value, not stale userProfile)
      const prevValue = userProfile?.default_rest_timer_seconds || 90;
      setRestTimerText(prevValue.toString());
      const errorMessage = error.response?.data?.detail || 'Failed to update rest timer';
      Alert.alert('Error', errorMessage);
    } finally {
      setUpdatingRestTimer(false);
      savingRestTimerRef.current = false;
    }
  };
  
  const handleRestTimerChange = (text: string) => {
    // ✅ Update text state immediately (allows smooth typing, including empty/backspace)
    setRestTimerText(text);
    
    // Clear existing timer
    if (restTimerDebounceRef.current) {
      clearTimeout(restTimerDebounceRef.current);
    }
    
    // Parse number only for validation (don't block typing)
    const num = parseInt(text, 10);
    if (isNaN(num) || num < 0) {
      // Invalid input - don't save, but allow typing
      return;
    }
    
    // Debounce: Save after 500ms of no typing
    restTimerDebounceRef.current = setTimeout(() => {
      saveRestTimer(num);
    }, 500);
  };

  const handleRestTimerBlur = async () => {
    // Save immediately on blur (don't wait for debounce)
    if (restTimerDebounceRef.current) {
      clearTimeout(restTimerDebounceRef.current);
      restTimerDebounceRef.current = null;
    }
    
    // Parse and save immediately
    const num = parseInt(restTimerText, 10);
    if (!isNaN(num) && num >= 0) {
      await saveRestTimer(num);
    } else {
      // Invalid input on blur - revert to last saved value
      const prevValue = userProfile?.default_rest_timer_seconds || 90;
      setRestTimerText(prevValue.toString());
    }
  };

  const handleNotificationsToggle = async (value: boolean) => {
    const prev = notificationsEnabled;
    setNotificationsEnabled(value);
    try {
      setUpdatingNotifications(true);
      await pushApi.updatePreferences({ notifications_enabled: value });
      const profile = await userApi.getProfile();
      setUserProfile(profile);
      if (value) {
        await registerForPushNotifications();
      }
    } catch (error: unknown) {
      setNotificationsEnabled(prev);
      const msg = error && typeof (error as any).response?.data?.detail === 'string'
        ? (error as any).response.data.detail
        : 'Failed to update notifications';
      Alert.alert('Error', msg);
    } finally {
      setUpdatingNotifications(false);
    }
  };

  const handleSaveBody = async () => {
    const wRaw = weightKg.trim();
    const hRaw = heightCm.trim();
    const dob = dateOfBirth.trim() || null;
    const w = wRaw ? parseFloat(wRaw) : null;
    const h = hRaw ? parseFloat(hRaw) : null;
    if (w != null && (isNaN(w) || w < 0 || w > 500)) {
      Alert.alert('Invalid value', 'Weight must be between 0 and 500 kg.');
      return;
    }
    if (h != null && (isNaN(h) || h < 0 || h > 300)) {
      Alert.alert('Invalid value', 'Height must be between 0 and 300 cm.');
      return;
    }
    if (dob != null && !/^\d{4}-\d{2}-\d{2}$/.test(dob)) {
      Alert.alert('Invalid date', 'Date of birth must be YYYY-MM-DD.');
      return;
    }
    try {
      setUpdatingBody(true);
      const updated = await userApi.updateSettings({
        weight_kg: w,
        height_cm: h,
        date_of_birth: dob,
        gender: gender ?? null,
      });
      setUserProfile(updated);
    } catch (error: any) {
      const msg = error?.response?.data?.detail ?? 'Failed to update body info';
      Alert.alert('Error', msg);
    } finally {
      setUpdatingBody(false);
    }
  };

  const handleReminderTimeChange = async (newTime: string | null) => {
    setReminderTime(newTime);
    try {
      await pushApi.updatePreferences({
        reminder_time: newTime === '' ? null : newTime ?? undefined,
      });
      const profile = await userApi.getProfile();
      setUserProfile(profile);
    } catch (error: unknown) {
      const msg = error && typeof (error as any).response?.data?.detail === 'string'
        ? (error as any).response.data.detail
        : 'Failed to update reminder time';
      Alert.alert('Error', msg);
    }
  };

  const handlePrimaryGoalChange = async (goal: PrimaryGoalValue) => {
    if (goal === primaryGoal) return;
    const prev = primaryGoal;
    setPrimaryGoal(goal);
    try {
      setUpdatingGoal(true);
      await coachApi.updateProfile({ primary_goal: goal });
    } catch (error: unknown) {
      setPrimaryGoal(prev);
      const msg = error && typeof (error as any).response?.data?.detail === 'string'
        ? (error as any).response.data.detail
        : 'Failed to update goal';
      Alert.alert('Error', msg);
    } finally {
      setUpdatingGoal(false);
    }
  };

  const handleSendTestNotification = async () => {
    try {
      setSendingTest(true);
      await pushApi.sendTest();
      Alert.alert('Sent', 'Test notification sent to your device(s).');
    } catch (error: unknown) {
      const msg = error && typeof (error as any).response?.data?.detail === 'string'
        ? (error as any).response.data.detail
        : 'Failed to send test notification';
      Alert.alert('Error', msg);
    } finally {
      setSendingTest(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            // Navigation will be handled by AppNavigator based on isAuthenticated state
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* User Info Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Email</Text>
          <Text style={styles.value}>{userProfile?.email || '—'}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Account Created</Text>
          <Text style={styles.value}>
            {userProfile?.created_at
              ? new Date(userProfile.created_at).toLocaleDateString()
              : '—'}
          </Text>
        </View>
      </View>

      {/* Body & personal — for coach, plan, predictions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Body & personal</Text>
        <Text style={styles.hint}>Used by Coach, Plan, and insights for personalized advice.</Text>
        <View style={styles.settingRow}>
          <Text style={styles.label}>Weight (kg)</Text>
          <TextInput
            style={styles.input}
            value={weightKg}
            onChangeText={setWeightKg}
            keyboardType="decimal-pad"
            placeholder="e.g. 70"
            placeholderTextColor="#999"
          />
        </View>
        <View style={styles.settingRow}>
          <Text style={styles.label}>Height (cm)</Text>
          <TextInput
            style={styles.input}
            value={heightCm}
            onChangeText={setHeightCm}
            keyboardType="decimal-pad"
            placeholder="e.g. 175"
            placeholderTextColor="#999"
          />
        </View>
        <View style={styles.settingRow}>
          <Text style={styles.label}>Date of birth (YYYY-MM-DD)</Text>
          <TextInput
            style={styles.input}
            value={dateOfBirth}
            onChangeText={setDateOfBirth}
            placeholder="e.g. 1990-05-15"
            placeholderTextColor="#999"
          />
        </View>
        <View style={styles.settingRow}>
          <Text style={styles.label}>Gender</Text>
          <View style={styles.genderRow}>
            {(['male', 'female', 'other', 'prefer_not_say'] as const).map((g) => (
              <TouchableOpacity
                key={g}
                style={[
                  styles.genderChip,
                  gender === g && styles.genderChipActive,
                ]}
                onPress={() => setGender(gender === g ? null : g)}
              >
                <Text style={[
                  styles.genderChipText,
                  gender === g && styles.genderChipTextActive,
                ]}>
                  {g === 'prefer_not_say' ? 'Prefer not to say' : g.charAt(0).toUpperCase() + g.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton, updatingBody && styles.buttonDisabled]}
          onPress={handleSaveBody}
          disabled={updatingBody}
        >
          {updatingBody ? (
            <ActivityIndicator size="small" color="#007AFF" />
          ) : (
            <Text style={styles.secondaryButtonText}>Save body info</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Primary goal — drives timeline, coach, plan */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Primary goal</Text>
        <Text style={styles.hint}>Used by Coach, Plan, and Transformation Timeline.</Text>
        <View style={styles.goalRow}>
          {(
            [
              { value: 'general' as const, label: 'General fitness' },
              { value: 'strength' as const, label: 'Strength' },
              { value: 'muscle' as const, label: 'Muscle gain' },
              { value: 'weight_loss' as const, label: 'Weight loss' },
            ] as const
          ).map(({ value, label }) => (
            <TouchableOpacity
              key={value}
              style={[
                styles.goalChip,
                primaryGoal === value && styles.goalChipActive,
                updatingGoal && styles.goalChipDisabled,
              ]}
              onPress={() => handlePrimaryGoalChange(value)}
              disabled={updatingGoal}
            >
              {updatingGoal && primaryGoal === value ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={[styles.goalChipText, primaryGoal === value && styles.goalChipTextActive]}>
                  {label}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Training Plan — always visible (single mode) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Training</Text>
        <TouchableOpacity
          style={styles.linkRow}
          onPress={() => navigation.navigate('PlanDetails')}
        >
          <Text style={styles.label}>Training Plan</Text>
          <Text style={styles.linkArrow}>→</Text>
        </TouchableOpacity>
      </View>

      {/* Settings Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>
        
        {/* Units Toggle - ✅ Immediate persistence on change */}
        <View style={styles.settingRow}>
          <Text style={styles.label}>Weight Units</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleOption, 
                units === 'kg' && styles.toggleOptionActive,
                updatingUnits && styles.toggleOptionDisabled
              ]}
              onPress={() => handleUnitsChange('kg')}
              disabled={updatingUnits}
            >
              {updatingUnits && units === 'kg' ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={[styles.toggleText, units === 'kg' && styles.toggleTextActive]}>kg</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleOption, 
                units === 'lb' && styles.toggleOptionActive,
                updatingUnits && styles.toggleOptionDisabled
              ]}
              onPress={() => handleUnitsChange('lb')}
              disabled={updatingUnits}
            >
              {updatingUnits && units === 'lb' ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={[styles.toggleText, units === 'lb' && styles.toggleTextActive]}>lb</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Timezone - ✅ Read-only display + device detection button (NOT free-text) */}
        <View style={styles.settingRow}>
          <Text style={styles.label}>Timezone</Text>
          <View style={styles.timezoneContainer}>
            <Text style={styles.timezoneValue}>{timezone || 'Not set'}</Text>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, updatingTimezone && styles.buttonDisabled]}
              onPress={handleDetectTimezone}
              disabled={updatingTimezone}
            >
              {updatingTimezone ? (
                <ActivityIndicator size="small" color="#007AFF" />
              ) : (
                <Text style={styles.secondaryButtonText}>Detect from Device</Text>
              )}
            </TouchableOpacity>
          </View>
          {/* ⏳ Optional: Add "Change timezone" button → searchable picker (future enhancement) */}
        </View>

        {/* Rest Timer Input - ✅ Debounced save on blur, string state for smooth typing */}
        <View style={styles.settingRow}>
          <Text style={styles.label}>Default Rest Timer (seconds)</Text>
          <TextInput
            style={styles.input}
            value={restTimerText}
            onChangeText={handleRestTimerChange}
            onBlur={handleRestTimerBlur}
            keyboardType="numeric"
            placeholder="90"
          />
          {updatingRestTimer && (
            <Text style={styles.savingText}>Saving...</Text>
          )}
        </View>
      </View>

      {/* Notifications Section — always visible (single mode) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <View style={styles.settingRow}>
          <Text style={styles.label}>Push Notifications</Text>
          <Switch
            value={notificationsEnabled}
            onValueChange={handleNotificationsToggle}
            disabled={updatingNotifications}
          />
        </View>
        {notificationsEnabled && (
          <>
            <View style={styles.settingRow}>
              <Text style={styles.label}>Daily reminder time (HH:MM)</Text>
              <TextInput
                style={styles.input}
                value={reminderTime ?? ''}
                onChangeText={(text) => setReminderTime(text || null)}
                onBlur={() => {
                  const t = reminderTime?.trim();
                  if (t && /^\d{2}:\d{2}$/.test(t)) {
                    handleReminderTimeChange(t);
                  } else if (t === '') {
                    handleReminderTimeChange(null);
                  }
                }}
                placeholder="09:00"
                placeholderTextColor="#999"
              />
            </View>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, sendingTest && styles.buttonDisabled]}
              onPress={handleSendTestNotification}
              disabled={sendingTest}
            >
              {sendingTest ? (
                <ActivityIndicator size="small" color="#007AFF" />
              ) : (
                <Text style={styles.secondaryButtonText}>Send test notification</Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Build info — single mode */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Build info</Text>
        <View style={styles.infoRow}>
          <Text style={styles.label}>API</Text>
          <Text style={styles.value} numberOfLines={1}>{API_URL}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Version</Text>
          <Text style={styles.value}>{APP_VERSION}</Text>
        </View>
      </View>

      {/* Reset demo — for demo user only */}
      {userProfile?.email === DEMO_EMAIL && (
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={() => {
              Alert.alert(
                'Reset demo',
                'Log out and tap Try Demo again to start fresh.',
                [{ text: 'Cancel' }, { text: 'Log out', onPress: handleLogout }]
              );
            }}
          >
            <Text style={styles.secondaryButtonText}>Reset demo</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Logout Section */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.button, styles.logoutButton]}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
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
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  section: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#333',
  },
  hint: {
    fontSize: 12,
    color: '#666',
    marginBottom: 12,
  },
  genderRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  genderChip: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  genderChipActive: {
    backgroundColor: '#007AFF',
  },
  genderChipText: {
    fontSize: 14,
    color: '#333',
  },
  genderChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  goalRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  goalChip: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  goalChipActive: {
    backgroundColor: '#007AFF',
  },
  goalChipDisabled: {
    opacity: 0.7,
  },
  goalChipText: {
    fontSize: 14,
    color: '#333',
  },
  goalChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  linkArrow: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '500',
  },
  label: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  value: {
    fontSize: 14,
    color: '#333',
    fontWeight: '400',
  },
  settingRow: {
    marginBottom: 20,
  },
  toggleContainer: {
    flexDirection: 'row',
    marginTop: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 4,
  },
  toggleOption: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  toggleOptionActive: {
    backgroundColor: '#007AFF',
  },
  toggleOptionDisabled: {
    opacity: 0.6,
  },
  toggleText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#666',
  },
  toggleTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  timezoneContainer: {
    marginTop: 8,
  },
  timezoneValue: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
    padding: 12,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginTop: 8,
    backgroundColor: '#f9f9f9',
  },
  savingText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: '#ff4444',
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
