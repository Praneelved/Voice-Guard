import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Button } from './Button';
import { colors } from '../theme/colors';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState = ({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {onRetry && (
        <Button title="Try Again" onPress={onRetry} variant="primary" style={styles.button} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.danger,
    marginBottom: 8,
    textAlign: 'center',
  },
  message: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    minWidth: 120,
  }
});
