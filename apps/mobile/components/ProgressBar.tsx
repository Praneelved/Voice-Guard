import React from 'react';
import { View, StyleSheet, ViewProps } from 'react-native';
import { colors } from '../theme/colors';

interface ProgressBarProps extends ViewProps {
  progress: number; // 0 to 1
  color?: string;
}

export const ProgressBar = ({ progress, color = colors.primary, style, ...props }: ProgressBarProps) => {
  const safeProgress = Math.max(0, Math.min(1, progress));
  
  return (
    <View style={[styles.container, style]} {...props}>
      <View style={[styles.bar, { width: `${safeProgress * 100}%`, backgroundColor: color }]} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  bar: {
    height: '100%',
    borderRadius: 4,
  },
});
