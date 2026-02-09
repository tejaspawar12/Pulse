/**
 * Logger utility for controlled debug logging.
 * 
 * Enable debug logs by setting EXPO_PUBLIC_DEBUG_LOGS=true in .env
 * Debug logs are automatically disabled in production builds.
 */
const ENABLE_DEBUG_LOGS = __DEV__ && process.env.EXPO_PUBLIC_DEBUG_LOGS === 'true';

export const log = (...args: any[]) => {
  if (ENABLE_DEBUG_LOGS) console.log(...args);
};

export const warn = (...args: any[]) => {
  if (ENABLE_DEBUG_LOGS) console.warn(...args);
};

export const error = (...args: any[]) => {
  console.error(...args);
};
