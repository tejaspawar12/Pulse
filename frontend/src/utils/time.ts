/**
 * Time utility functions.
 */

/**
 * Compute elapsed seconds from start time.
 * CRITICAL: Handles NaN and invalid dates.
 */
export const computeElapsedSeconds = (startTime: string): number => {
  const start = new Date(startTime).getTime();
  
  // CRITICAL: Handle invalid startTime (NaN check)
  if (Number.isNaN(start)) {
    return 0;
  }
  
  const elapsedMs = Date.now() - start;
  
  // Handle negative elapsed (shouldn't happen, but defensive)
  if (elapsedMs < 0) {
    return 0;
  }
  
  return Math.max(0, Math.floor(elapsedMs / 1000));
};
