import { Tabs } from 'expo-router';
import { colors } from '../../theme/colors';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ 
      headerShown: true,
      headerStyle: { backgroundColor: colors.surface },
      headerTintColor: colors.text,
      tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.textMuted,
    }}>
      <Tabs.Screen name="home" options={{ title: 'Home' }} />
      <Tabs.Screen name="alerts" options={{ title: 'Alerts' }} />
      <Tabs.Screen name="history" options={{ title: 'History' }} />
      <Tabs.Screen name="trusted-voices" options={{ title: 'Trusted' }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
    </Tabs>
  );
}
