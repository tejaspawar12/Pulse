/**
 * Push subscription and notification preferences API.
 */
import { apiClient } from './client';

export interface RegisterPushTokenRequest {
  push_token: string;
  platform: 'ios' | 'android';
}

export interface PushSubscriptionOut {
  id: string;
  user_id: string;
  platform: string;
  is_active: boolean;
}

export const pushApi = {
  registerToken: async (data: RegisterPushTokenRequest): Promise<PushSubscriptionOut> => {
    const response = await apiClient.post<PushSubscriptionOut>(
      '/users/me/push-subscriptions',
      data
    );
    return response.data;
  },

  unsubscribe: async (subscriptionId: string): Promise<void> => {
    await apiClient.delete(`/users/me/push-subscriptions/${subscriptionId}`);
  },

  updatePreferences: async (data: {
    notifications_enabled?: boolean;
    reminder_time?: string | null;
  }): Promise<void> => {
    await apiClient.patch('/users/me/notification-preferences', data);
  },

  sendTest: async (): Promise<void> => {
    await apiClient.post('/users/me/push-subscriptions/test-send');
  },

  getSubscriptions: async (): Promise<PushSubscriptionOut[]> => {
    const response = await apiClient.get<PushSubscriptionOut[]>('/users/me/push-subscriptions');
    return response.data;
  },
};
