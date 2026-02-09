/**
 * Login Screen.
 */
import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert, 
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { authApi } from '../services/api/auth.api';
import { userApi } from '../services/api/user.api';
import { useUserStore } from '../store/userStore';
import { useWorkoutStore } from '../store/workoutStore';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { AuthStackParamList } from '../navigation/types'; // ✅ Define types once, reuse everywhere
import { isPortfolioMode } from '../config/constants'; // single mode: always true (Try Demo + full UI)

type NavigationProp = StackNavigationProp<AuthStackParamList>;

export const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  
  const login = useUserStore((state) => state.login);
  const navigation = useNavigation<NavigationProp>();

  const validate = (): boolean => {
    const newErrors: { email?: string; password?: string } = {};
    
    // ⚠️ CRITICAL: Minimal validation only (backend uses EmailStr for proper validation)
    // Don't use custom regex (often rejects valid emails)
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;
    
    try {
      setLoading(true);
      const response = await authApi.login({
        email: email.trim(),
        password,
      });
      await completeLogin(response);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Invalid email or password';
      Alert.alert('Login Failed', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /** Phase 3: Try Demo — log in as demo user (no credentials). */
  const handleTryDemo = async () => {
    try {
      setLoading(true);
      const response = await authApi.demoLogin();
      await completeLogin(response);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Demo login failed. Is the backend running?';
      Alert.alert('Try Demo Failed', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const completeLogin = async (response: { access_token: string; refresh_token: string; user: any }) => {
    await login(response.access_token, response.user);
    await SecureStore.setItemAsync('fitnesscoach.refresh_token', response.refresh_token);
    try {
      useWorkoutStore.getState().clearActiveWorkout();
      useWorkoutStore.getState().setLoaded(false);
      const status = await userApi.getStatus();
      useUserStore.getState().setUserStatus(status);
    } catch (e) {
      console.warn('Post-login status refresh failed', e);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.content}>
          <Text style={styles.title}>{isPortfolioMode ? 'Workout Tracker' : 'Login'}</Text>
          <Text style={styles.subtitle}>
            {isPortfolioMode ? 'Try the demo or sign in with your account' : 'Welcome back!'}
          </Text>
          
          {isPortfolioMode && (
            <>
              <TouchableOpacity
                style={[styles.button, styles.demoButton, loading && styles.buttonDisabled]}
                onPress={handleTryDemo}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.buttonText}>Try Demo</Text>
                )}
              </TouchableOpacity>
              <Text style={styles.formLabel}>Or sign in with your account</Text>
            </>
          )}
          
          <View style={styles.form}>
            <TextInput
              style={[styles.input, errors.email && styles.inputError]}
              placeholder="Email"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                if (errors.email) setErrors({ ...errors, email: undefined });
              }}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
            />
            {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}
            
            <TextInput
              style={[styles.input, errors.password && styles.inputError]}
              placeholder="Password"
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                if (errors.password) setErrors({ ...errors, password: undefined });
              }}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="password"
            />
            {errors.password && <Text style={styles.errorText}>{errors.password}</Text>}
            
            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Login</Text>
              )}
            </TouchableOpacity>
            
            {!isPortfolioMode && (
              <TouchableOpacity
                style={styles.linkButton}
                onPress={() => navigation.navigate('Register')}
              >
                <Text style={styles.linkText}>Don't have an account? Register</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 32,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
    backgroundColor: '#f9f9f9',
  },
  inputError: {
    borderColor: '#ff4444',
  },
  errorText: {
    color: '#ff4444',
    fontSize: 12,
    marginTop: -12,
    marginBottom: 16,
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
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  linkText: {
    color: '#007AFF',
    fontSize: 14,
  },
  demoButton: {
    backgroundColor: '#34C759',
    marginBottom: 24,
  },
  formLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
});
