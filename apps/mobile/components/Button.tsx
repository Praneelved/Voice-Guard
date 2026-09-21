import React from 'react';
import { TouchableOpacity, Text, StyleSheet, TouchableOpacityProps, ActivityIndicator } from 'react-native';
import { colors } from '../theme/colors';

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'warning';
  isLoading?: boolean;
}

export const Button = ({ title, variant = 'primary', isLoading, style, ...props }: ButtonProps) => {
  const backgroundColor = 
    variant === 'primary' ? colors.primary :
    variant === 'danger' ? colors.danger : 
    variant === 'warning' ? colors.warning : colors.surface;
    
  return (
    <TouchableOpacity 
      style={[styles.button, { backgroundColor }, style]} 
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? (
        <ActivityIndicator color={colors.text} />
      ) : (
        <Text style={styles.text}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  text: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
});
