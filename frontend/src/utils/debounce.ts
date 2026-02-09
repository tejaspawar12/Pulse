/**
 * Debounce utility for delaying function execution.
 * Includes cancel() method for cleanup.
 * 
 * @param func Function to debounce
 * @param wait Wait time in milliseconds
 * @returns Debounced function with cancel() method
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) & { cancel: () => void } {
  let timeout: NodeJS.Timeout | null = null;

  const debounced = function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  } as ((...args: Parameters<T>) => void) & { cancel: () => void };

  // Add cancel method
  debounced.cancel = () => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
    }
  };

  return debounced;
}
