import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, EmptyState, Badge, ErrorState } from '../../components';
import { colors } from '../../theme/colors';
import { Alert } from '../../types';
import { useAlerts } from '../../hooks/api/useAlerts';

export default function AlertsScreen() {
  const router = useRouter();
  const { data: alerts, isLoading, error, refetch } = useAlerts();

  if (error) {
    return (
      <ScreenContainer safeArea={false}>
        <ErrorState 
          title="Failed to Load Alerts" 
          message="We couldn't connect to the server." 
          onRetry={refetch} 
        />
      </ScreenContainer>
    );
  }

  if (isLoading) {
    return (
      <ScreenContainer safeArea={false} style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </ScreenContainer>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <ScreenContainer safeArea={false}>
        <EmptyState 
          title="No Active Alerts" 
          message="Your calls are safe. Any suspicious activity will appear here."
        />
      </ScreenContainer>
    );
  }

  const renderAlert = (alert: Alert) => (
    <TouchableOpacity 
      key={alert.id} 
      style={styles.alertCard}
      onPress={() => router.push(`/alerts/${alert.id}`)}
    >
      <View style={styles.header}>
        <Text style={styles.caller}>{alert.callerNumber}</Text>
        <Badge 
          label={alert.severity.toUpperCase()} 
          variant={alert.severity === 'critical' ? 'danger' : alert.severity === 'warning' ? 'warning' : 'info'} 
        />
      </View>
      <View style={styles.details}>
        <Text style={styles.detailText}>Risk: {alert.riskLevel}</Text>
        <Text style={styles.detailText}>Verified: {alert.verificationStatus}</Text>
      </View>
      <Text style={styles.timestamp}>{new Date(alert.timestamp).toLocaleString()}</Text>
    </TouchableOpacity>
  );

  return (
    <ScreenContainer safeArea={false}>
      <ScrollView contentContainerStyle={styles.container}>
        {alerts.map(renderAlert)}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  center: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  container: {
    padding: 16,
    gap: 12,
  },
  alertCard: {
    backgroundColor: colors.surface,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: colors.danger,
    borderWidth: 1,
    borderColor: colors.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  caller: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailText: {
    color: colors.text,
    fontSize: 14,
  },
  timestamp: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'right',
  }
});
