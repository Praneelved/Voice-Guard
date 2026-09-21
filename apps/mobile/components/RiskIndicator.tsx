import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ProgressBar } from './ProgressBar';
import { colors } from '../theme/colors';

interface RiskIndicatorProps {
  score: number; // 0 to 100
}

export const RiskIndicator = ({ score }: RiskIndicatorProps) => {
  const getRiskColor = (s: number) => {
    if (s < 30) return colors.riskLow;
    if (s < 70) return colors.riskMedium;
    if (s < 90) return colors.riskHigh;
    return colors.riskCritical;
  };

  const getRiskLabel = (s: number) => {
    if (s < 30) return 'Safe';
    if (s < 70) return 'Warning';
    if (s < 90) return 'High Risk';
    return 'Critical';
  };

  const color = getRiskColor(score);
  
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.label}>Rolling Risk Score</Text>
        <Text style={[styles.score, { color }]}>{score.toFixed(1)} / 100 ({getRiskLabel(score)})</Text>
      </View>
      <ProgressBar progress={score / 100} color={color} style={styles.progress} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: {
    color: colors.textMuted,
    fontSize: 14,
  },
  score: {
    fontWeight: 'bold',
    fontSize: 14,
  },
  progress: {
    height: 12,
  },
});
