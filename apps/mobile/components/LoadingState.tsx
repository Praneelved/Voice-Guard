import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState = ({ message = 'Loading...' }: LoadingStateProps) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={styles.message}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  message: {
    marginTop: 16,
    color: colors.textMuted,
    fontSize: 14,
  },
});
