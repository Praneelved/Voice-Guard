import React from 'react';
import { View, Text, StyleSheet, ViewProps } from 'react-native';
import { colors } from '../theme/colors';

interface BadgeProps extends ViewProps {
  label: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'default';
}

export const Badge = ({ label, variant = 'default', style, ...props }: BadgeProps) => {
  const getBackgroundColor = () => {
    switch (variant) {
      case 'success': return colors.success;
      case 'warning': return colors.warning;
      case 'danger': return colors.danger;
      case 'info': return colors.info;
      default: return colors.surface;
    }
  };

  return (
    <View style={[styles.badge, { backgroundColor: getBackgroundColor() }, style]} {...props}>
      <Text style={styles.text}>{label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  text: {
    color: colors.text,
    fontSize: 12,
    fontWeight: 'bold',
  },
});
