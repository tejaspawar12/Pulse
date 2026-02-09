/**
 * API client with JWT auth and refresh token retry.
 * Phase 2 Week 1: On 401, try refresh token once; do not intercept /auth/refresh (avoids loop).
 * Refresh is done via raw axios here to avoid require cycle: client.ts <-> auth.api.ts
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { secureStorage } from '../../utils/secureStorage';
import { useUserStore } from '../../store/userStore';

const API_V1 = '/api/v1';

function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && (window.location?.hostname === 'localhost' || window.location?.hostname === '127.0.0.1')) {
    return `http://localhost:8000${API_V1}`;
  }
  const env = process.env.EXPO_PUBLIC_API_URL?.trim() || '';
  if (!env) return `http://localhost:8000${API_V1}`;
  const base = env.replace(/\/+$/, '');
  return base.endsWith(API_V1) ? base : `${base}${API_V1}`;
}
const API_BASE_URL = getApiBaseUrl();

const REFRESH_TOKEN_KEY = 'fitnesscoach.refresh_token';

// Refresh token mutex: one in-flight refresh for all concurrent 401s
let refreshPromise: Promise<string> | null = null;

async function getNewAccessToken(): Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = (async () => {
    const refreshToken = await secureStorage.getItemAsync(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    // Use raw axios to avoid importing auth.api (breaks require cycle client <-> auth.api)
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
      { headers: { 'Content-Type': 'application/json' }, timeout: 15000 }
    );
    const { access_token, refresh_token: newRefreshToken } = data;
    useUserStore.getState().setAuthToken(access_token);
    await secureStorage.setItemAsync(REFRESH_TOKEN_KEY, newRefreshToken);
    return access_token;
  })().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      async (config) => {
        config.headers = config.headers ?? {};
        const state = useUserStore.getState();
        const token = state.authToken;

        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        } else if (__DEV__) {
          const userId = await AsyncStorage.getItem('dev_user_id');
          if (userId) {
            config.headers['X-DEV-USER-ID'] = userId;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          // Do not retry /auth/refresh — prevents infinite loop when refresh returns 401
          if (originalRequest.url?.includes('/auth/refresh')) {
            return Promise.reject(error);
          }

          originalRequest._retry = true;

          try {
            const newAccessToken = await getNewAccessToken();
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            try {
              await secureStorage.deleteItemAsync(REFRESH_TOKEN_KEY);
            } catch (_e) {
              // ignore
            }
            useUserStore.getState().logout();
            return Promise.reject(refreshError);
          }
        }

        if (!error.response) {
          console.error('Network error:', error.message);
          console.error('Request URL:', originalRequest?.url);
          throw new Error('Network error: Please check your connection');
        }

        if (error.response.status === 429) {
          const message =
            typeof error.response?.data?.detail === 'string'
              ? error.response.data.detail
              : 'Please wait a moment and try again.';
          Alert.alert('Too Many Requests', message, [{ text: 'OK' }]);
          return Promise.reject(error);
        }

        if (error.response.status >= 500) {
          console.error('Server error:', {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data,
            url: originalRequest?.url,
          });
        }

        return Promise.reject(error);
      }
    );
  }

  get instance(): AxiosInstance {
    return this.client;
  }
}

export const apiClient = new ApiClient().instance;
