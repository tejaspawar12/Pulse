/**
 * User types matching backend schemas.
 */

export interface User {
  id: string;
  email: string;
  units: 'kg' | 'lb';
  timezone: string;
  default_rest_timer_seconds: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  // Body / personal (for coach, plan, predictions)
  weight_kg?: number | null;
  height_cm?: number | null;
  date_of_birth?: string | null; // YYYY-MM-DD
  gender?: string | null; // male, female, other, prefer_not_say
  // Phase 2 Week 1 — entitlement / email verification
  email_verified?: boolean;
  entitlement?: 'free' | 'pro';
  pro_trial_ends_at?: string | null; // ISO datetime
  trial_used?: boolean;
  // Phase 2 Week 2 — notification preferences
  notifications_enabled?: boolean;
  reminder_time?: string | null; // "HH:MM"
}
