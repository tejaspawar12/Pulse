/**
 * Hook to get user's preferred weight unit.
 * Returns 'kg' as default if user profile not loaded yet.
 */
import { useUserStore } from '../store/userStore';

export const useUserUnit = (): 'kg' | 'lb' => {
  return useUserStore((state) => state.userProfile?.units ?? 'kg');
};
