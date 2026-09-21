import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Badge } from './Badge';
import { colors } from '../theme/colors';

interface SignalIndicatorProps {
  label: string;
  status: 'safe' | 'warning' | 'danger' | 'unknown' | 'verifying' | 'verified' | 'mismatch' | 'good' | 'poor';
}

export const SignalIndicator = ({ label, status }: SignalIndicatorProps) => {
  const getBadgeVariant = () => {
    switch (status) {
      case 'safe':
      case 'verified':
      case 'good':
        return 'success';
      case 'warning':
      case 'verifying':
      case 'poor':
        return 'warning';
      case 'danger':
      case 'mismatch':
        return 'danger';
      default:
        return 'default';
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <Badge label={status.toUpperCase()} variant={getBadgeVariant()} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  label: {
    color: colors.text,
    fontSize: 16,
  },
});
