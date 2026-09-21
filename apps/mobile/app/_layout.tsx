import React, { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../stores/useAuthStore';
import { StatusBar } from 'expo-status-bar';

const queryClient = new QueryClient();

export default function RootLayout() {
  const { isAuthenticated } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    const inAuthGroup = segments[0] === '(auth)';
    
    if (!isAuthenticated && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      router.replace('/(tabs)/home');
    }
  }, [isAuthenticated, segments, router]);

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
