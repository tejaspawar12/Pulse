import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { useEffect, useRef, useState } from 'react';
import { pushApi } from '../services/api/push.api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export function usePushNotifications() {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const listenerRef = useRef<Notifications.EventSubscription | null>(null);

  const registerForPushNotifications = async (): Promise<string | null> => {
    if (!Device.isDevice) {
      setError('Push notifications require a physical device');
      return null;
    }
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      setError('Permission not granted for push notifications');
      return null;
    }
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
      });
    }
    try {
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: Constants.expoConfig?.extra?.eas?.projectId,
      });
      const token = tokenData.data;
      setExpoPushToken(token);
      setError(null);
      await pushApi.registerToken({
        push_token: token,
        platform: Platform.OS as 'ios' | 'android',
      });
      return token;
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to get push token';
      setError(message);
      return null;
    }
  };

  useEffect(() => {
    listenerRef.current = Notifications.addNotificationReceivedListener(() => {});
    return () => {
      if (listenerRef.current?.remove) {
        listenerRef.current.remove();
      }
      listenerRef.current = null;
    };
  }, []);

  return { registerForPushNotifications, expoPushToken, error };
}
