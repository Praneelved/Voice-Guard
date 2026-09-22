import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { apiClient } from './api/client';

export class PushNotificationService {
  /**
   * Configures the behavior when a notification is received while the app is in the foreground.
   */
  static configureForegroundHandler() {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    });
  }

  /**
   * Requests permission and registers the push token with the backend.
   */
  static async registerForPushNotificationsAsync() {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    if (!Device.isDevice) {
      console.log('Must use physical device for Push Notifications');
      return null;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.log('Failed to get push token for push notification!');
      return null;
    }

    try {
      // EAS Project ID is required by expo-notifications
      const projectId =
        Constants?.expoConfig?.extra?.eas?.projectId ??
        Constants?.easConfig?.projectId;
        
      if (!projectId) {
         console.warn('Project ID not found in app.json. Add expo.extra.eas.projectId to enable push notifications.');
      }

      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId,
      });
      const pushToken = tokenData.data;

      // Register with Backend
      await apiClient.post('/v1/users/devices', {
        push_token: pushToken,
        platform: Platform.OS
      });

      console.log('Push token successfully registered:', pushToken);
      return pushToken;
    } catch (e) {
      console.warn('Error fetching or registering push token:', e);
      return null;
    }
  }
}
