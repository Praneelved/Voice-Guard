import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ScreenContainer, Button } from '../../components';
import { colors } from '../../theme/colors';

export default function AlertDetailsScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();

  return (
    <ScreenContainer style={styles.container}>
      <Text style={styles.title}>Alert Details</Text>
      <Text style={styles.id}>ID: {id}</Text>
      
      <Button title="Go Back" onPress={() => router.back()} style={styles.btn} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  id: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 24,
  },
  btn: {
    minWidth: 120,
  }
});
