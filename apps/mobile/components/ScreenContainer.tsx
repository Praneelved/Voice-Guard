import React from 'react';
import { View, StyleSheet, ViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../theme/colors';

interface ScreenContainerProps extends ViewProps {
  children: React.ReactNode;
  safeArea?: boolean;
}

export const ScreenContainer = ({ children, safeArea = true, style, ...props }: ScreenContainerProps) => {
  const Container = safeArea ? SafeAreaView : View;
  
  return (
    <Container style={[styles.container, style]} {...props}>
      {children}
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
});
