import React from 'react';
import { View, StyleSheet, ViewProps } from 'react-native';
import { colors } from '../theme/colors';

export const Card = ({ children, style, ...props }: ViewProps) => {
  return (
    <View style={[styles.card, style]} {...props}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
});
