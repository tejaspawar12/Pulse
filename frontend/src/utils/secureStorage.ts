/**
 * Secure storage abstraction: SecureStore on native, localStorage on web.
 * expo-secure-store is not available on web (no getItemAsync/setItemAsync/deleteItemAsync).
 */
import { Platform } from 'react-native';

const isWeb = Platform.OS === 'web';

async function webGet(key: string): Promise<string | null> {
  if (typeof window === 'undefined' || !window.localStorage) return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

async function webSet(key: string, value: string): Promise<void> {
  if (typeof window === 'undefined' || !window.localStorage) return;
  window.localStorage.setItem(key, value);
}

async function webDelete(key: string): Promise<void> {
  if (typeof window === 'undefined' || !window.localStorage) return;
  window.localStorage.removeItem(key);
}

export const secureStorage = {
  async getItemAsync(key: string): Promise<string | null> {
    if (isWeb) return webGet(key);
    try {
      const SecureStore = require('expo-secure-store').default;
      return await SecureStore.getItemAsync(key);
    } catch (e) {
      if (__DEV__) console.warn('secureStorage.getItemAsync failed (native):', e);
      return null;
    }
  },
  async setItemAsync(key: string, value: string): Promise<void> {
    if (isWeb) return webSet(key, value);
    try {
      const SecureStore = require('expo-secure-store').default;
      await SecureStore.setItemAsync(key, value);
    } catch (e) {
      if (__DEV__) console.warn('secureStorage.setItemAsync failed (native):', e);
    }
  },
  async deleteItemAsync(key: string): Promise<void> {
    if (isWeb) return webDelete(key);
    try {
      const SecureStore = require('expo-secure-store').default;
      await SecureStore.deleteItemAsync(key);
    } catch (e) {
      if (__DEV__) console.warn('secureStorage.deleteItemAsync failed (native):', e);
    }
  },
};
