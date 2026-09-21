import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../components';
import { colors } from '../theme/colors';

export default function EnrollmentScreen() {
  const router = useRouter();

  return (
    <ScreenContainer style={styles.container}>
      <Text style={styles.title}>Enroll Trusted Voice</Text>
      <Text style={styles.description}>
        Read the following phrase clearly into your microphone to create a secure voice profile.
      </Text>
      
      <View style={styles.phraseBox}>
        <Text style={styles.phrase}>"My voice is my secure password to authorize this action."</Text>
      </View>
      
      <View style={styles.actions}>
        <Button title="Start Recording" onPress={() => router.back()} />
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
    color: colors.primary,
    marginBottom: 16,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 32,
  },
  phraseBox: {
    backgroundColor: colors.surface,
    padding: 24,
    borderRadius: 12,
    marginBottom: 48,
    borderWidth: 1,
    borderColor: colors.border,
  },
  phrase: {
    fontSize: 18,
    fontStyle: 'italic',
    color: colors.text,
    textAlign: 'center',
    lineHeight: 28,
  },
  actions: {
    gap: 16,
  }
});
