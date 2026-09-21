import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../../components';
import { colors } from '../../theme/colors';

export default function PrivacySettingsScreen() {
  const router = useRouter();

  return (
    <ScreenContainer style={styles.container}>
      <Text style={styles.title}>Privacy Settings</Text>
      
      <View style={styles.content}>
        <Text style={styles.text}>Configure your data sharing and privacy preferences.</Text>
      </View>

      <Button title="Go Back" onPress={() => router.back()} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 24,
  },
  content: {
    flex: 1,
  },
  text: {
    color: colors.textMuted,
    fontSize: 16,
  }
});
