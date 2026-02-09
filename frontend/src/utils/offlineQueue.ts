/**
 * Offline queue utility for set EDIT/DELETE operations.
 * 
 * LOCKED: Option A - Only queue set EDIT/DELETE (not ADD)
 * - Adding sets requires network to get new set IDs
 * - Exercise add/delete and workout finish require network (show error)
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

export type OfflineQueueAction = 'edit_set' | 'delete_set';

export interface OfflineQueueItem {
  action: OfflineQueueAction;
  set_id: string;
  data?: any; // For edit_set: { reps?, weight?, set_type?, rpe?, rest_time_seconds? }
  timestamp: number;
}

const QUEUE_STORAGE_KEY = 'offline_queue';

/**
 * Add item to offline queue.
 */
export const addToQueue = async (item: OfflineQueueItem): Promise<void> => {
  try {
    const queue = await getQueue();
    queue.push(item);
    await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
  } catch (error) {
    console.error('[offlineQueue] Error adding to queue:', error);
    throw error;
  }
};

/**
 * Get all items from offline queue.
 */
export const getQueue = async (): Promise<OfflineQueueItem[]> => {
  try {
    const data = await AsyncStorage.getItem(QUEUE_STORAGE_KEY);
    if (!data) return [];
    return JSON.parse(data);
  } catch (error) {
    console.error('[offlineQueue] Error getting queue:', error);
    return [];
  }
};

/**
 * Remove item from queue (after successful retry).
 */
export const removeFromQueue = async (item: OfflineQueueItem): Promise<void> => {
  try {
    const queue = await getQueue();
    const filtered = queue.filter(
      (q) => !(q.set_id === item.set_id && q.action === item.action && q.timestamp === item.timestamp)
    );
    await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('[offlineQueue] Error removing from queue:', error);
    throw error;
  }
};

/**
 * Clear entire queue.
 */
export const clearQueue = async (): Promise<void> => {
  try {
    await AsyncStorage.removeItem(QUEUE_STORAGE_KEY);
  } catch (error) {
    console.error('[offlineQueue] Error clearing queue:', error);
    throw error;
  }
};
