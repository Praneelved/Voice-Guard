import React, { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../stores/useAuthStore';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator } from 'react-native';
import * as Notifications from 'expo-notifications';
import { PushNotificationService } from '../services/PushNotificationService';

const queryClient = new QueryClient();

export default function RootLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    const inAuthGroup = segments[0] === '(auth)';
    
    if (!isAuthenticated && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      router.replace('/(tabs)/home');
    }

    if (isAuthenticated) {
      // Register for push notifications when authenticated
      PushNotificationService.configureForegroundHandler();
      PushNotificationService.registerForPushNotificationsAsync();
    }
  }, [isAuthenticated, isLoading, segments, router]);

  useEffect(() => {
    // Handle tapping a push notification
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      // Assuming a generic route for active call, or extract ID if passed in notification payload
      router.push('/call/live');
    });
    
    return () => {
      Notifications.removeNotificationSubscription(responseListener);
    };
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#111827' }}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="call/live" />
        <Stack.Screen name="call/[id]" />
        <Stack.Screen name="alerts/[id]" />
        <Stack.Screen name="verification" />
        <Stack.Screen name="enrollment" />
        <Stack.Screen name="settings/privacy" />
        <Stack.Screen name="settings/profile" />
      </Stack>
    </QueryClientProvider>
  );
}
