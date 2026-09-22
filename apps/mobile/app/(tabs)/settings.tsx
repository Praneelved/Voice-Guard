import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../../components';
import { useAuthStore } from '../../stores/useAuthStore';
import { colors } from '../../theme/colors';

export default function SettingsScreen() {
  const router = useRouter();
  const logout = useAuthStore(state => state.logout);

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  return (
    <ScreenContainer safeArea={false} style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Button title="Security" variant="secondary" onPress={() => {}} style={styles.btn} />
        <Button title="Privacy" variant="secondary" onPress={() => router.push('/settings/privacy')} style={styles.btn} />
        <Button title="Notifications" variant="secondary" onPress={() => {}} style={styles.btn} />
        <Button title="Account" variant="secondary" onPress={() => router.push('/settings/profile')} style={styles.btn} />
        <Button title="Organization" variant="secondary" onPress={() => {}} style={styles.btn} />
        <Button title="About VoiceGuard" variant="secondary" onPress={() => {}} style={styles.btn} />
        
        <View style={styles.divider} />
        <Button title="Logout" variant="danger" onPress={handleLogout} style={styles.btn} />
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  btn: {
    justifyContent: 'flex-start',
    backgroundColor: colors.surface,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: 16,
  }
});
