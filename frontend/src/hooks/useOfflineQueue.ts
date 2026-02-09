/**
 * Hook for processing offline queue.
 */
import { useEffect, useState } from 'react';
import { getQueue, removeFromQueue, OfflineQueueItem } from '../utils/offlineQueue';
import { workoutApi } from '../services/api/workout.api';

/**
 * Check if network error occurred.
 * Network errors typically have no response object.
 */
const isNetworkError = (error: any): boolean => {
  return !error.response && (error.message?.includes('Network') || error.code === 'NETWORK_ERROR' || error.message?.includes('timeout'));
};

export const useOfflineQueue = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [queueLength, setQueueLength] = useState(0);

  const processQueue = async () => {
    const queue = await getQueue();
    setQueueLength(queue.length);
    
    if (queue.length === 0) return;
    
    setIsProcessing(true);
    
    try {
      // Process queue FIFO
      for (const item of queue) {
        try {
          if (item.action === 'edit_set') {
            await workoutApi.updateSet(item.set_id, item.data || {});
            console.log('[useOfflineQueue] Successfully processed edit_set:', item.set_id);
            // Remove from queue on success
            await removeFromQueue(item);
          } else if (item.action === 'delete_set') {
            await workoutApi.deleteSet(item.set_id);
            console.log('[useOfflineQueue] Successfully processed delete_set:', item.set_id);
            // Remove from queue on success
            await removeFromQueue(item);
          }
        } catch (error: any) {
          // If it's a network error, keep in queue for retry
          if (isNetworkError(error)) {
            console.log('[useOfflineQueue] Network error, keeping item in queue:', item);
            // Keep item in queue for retry
          } else {
            // Other errors (validation, etc.) - remove from queue to prevent infinite retries
            console.error('[useOfflineQueue] Non-network error, removing from queue:', item, error);
            await removeFromQueue(item);
          }
        }
      }
      
      // Update queue length after processing
      const remainingQueue = await getQueue();
      setQueueLength(remainingQueue.length);
    } finally {
      setIsProcessing(false);
    }
  };

  // Process queue periodically and on mount
  useEffect(() => {
    // Process on mount
    processQueue();
    
    // Process every 5 seconds if queue has items
    const interval = setInterval(() => {
      getQueue().then((queue) => {
        if (queue.length > 0) {
          processQueue();
        }
      });
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    processQueue,
    isProcessing,
    queueLength,
  };
};
