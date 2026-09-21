import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../../components';
import { useAuthStore } from '../../stores/useAuthStore';
import { colors } from '../../theme/colors';

export default function LoginScreen() {
  const router = useRouter();
  const login = useAuthStore(state => state.login);

  const handleLogin = () => {
    login({ id: '1', email: 'test@example.com', name: 'Test User' });
    router.replace('/(tabs)/home');
  };

  return (
    <ScreenContainer style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>VoiceGuard</Text>
        <Text style={styles.subtitle}>Sign in to your account</Text>
        
        <View style={styles.form}>
          <Button title="Login (Mock)" onPress={handleLogin} />
          <Button 
            title="Create an account" 
            variant="secondary" 
            onPress={() => router.push('/(auth)/register')} 
            style={styles.registerBtn}
          />
        </View>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    padding: 24,
  },
  content: {
    width: '100%',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.primary,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 48,
  },
  form: {
    gap: 16,
  },
  registerBtn: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.border,
  }
});
