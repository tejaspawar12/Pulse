/**
 * Date utility functions.
 * Standardized date parsing and formatting across the app.
 */

/**
 * Parse YYYY-MM-DD date string as local date.
 * ⚠️ CRITICAL: Prevents timezone shift bug when using new Date("2026-01-30")
 * 
 * @param ymd Date string in YYYY-MM-DD format
 * @returns Date object at local midnight
 */
export function parseLocalYMD(ymd: string): Date {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Date(y, m - 1, d); // Local midnight (prevents timezone shift)
}

/**
 * Format date as "Jan 30" (month and day only).
 * 
 * @param date Date object
 * @returns Formatted date string (e.g., "Jan 30")
 */
export function formatMonthDay(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Format date as "Jan 30, 2026" (full date).
 * 
 * @param date Date object
 * @returns Formatted date string (e.g., "Jan 30, 2026")
 */
export function formatFullDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

/**
 * Check if date is today (local date).
 * 
 * @param date Date object
 * @returns True if date is today
 */
export function isToday(date: Date): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const compareDate = new Date(date);
  compareDate.setHours(0, 0, 0, 0);
  return compareDate.getTime() === today.getTime();
}

/**
 * Check if date is yesterday (local date).
 * 
 * @param date Date object
 * @returns True if date is yesterday
 */
export function isYesterday(date: Date): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const compareDate = new Date(date);
  compareDate.setHours(0, 0, 0, 0);
  return compareDate.getTime() === yesterday.getTime();
}
