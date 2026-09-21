import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../components';
import { colors } from '../theme/colors';

export default function VerificationScreen() {
  const router = useRouter();

  return (
    <ScreenContainer style={styles.container}>
      <Text style={styles.title}>Verification Challenge</Text>
      <Text style={styles.description}>
        We detected high risk on this call. Ask the caller to repeat a specific phrase to verify their identity.
      </Text>
      
      <View style={styles.actions}>
        <Button title="Trigger Audio Challenge" onPress={() => router.back()} />
        <Button title="Cancel" variant="secondary" onPress={() => router.back()} />
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.danger,
    marginBottom: 16,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: colors.text,
    textAlign: 'center',
    marginBottom: 48,
  },
  actions: {
    gap: 16,
  }
});
