import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../../components';
import { colors } from '../../theme/colors';

export default function RegisterScreen() {
  const router = useRouter();

  return (
    <ScreenContainer style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Join VoiceGuard today</Text>
        
        <View style={styles.form}>
          <Button title="Register (Mock)" onPress={() => router.back()} />
          <Button 
            title="Back to login" 
            variant="secondary" 
            onPress={() => router.back()} 
            style={styles.backBtn}
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
  backBtn: {
    backgroundColor: 'transparent',
  }
});
