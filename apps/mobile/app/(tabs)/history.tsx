import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, EmptyState, Badge, ErrorState } from '../../components';
import { colors } from '../../theme/colors';
import { Call } from '../../types';
import { useCalls } from '../../hooks/api/useCalls';

export default function HistoryScreen() {
  const router = useRouter();
  const { data: calls, isLoading, error, refetch } = useCalls();

  if (error) {
    return (
      <ScreenContainer safeArea={false}>
        <ErrorState 
          title="Failed to Load History" 
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

  if (!calls || calls.length === 0) {
    return (
      <ScreenContainer safeArea={false}>
        <EmptyState 
          title="No Call History" 
          message="You haven't made any protected calls yet."
        />
      </ScreenContainer>
    );
  }

  const renderCall = (call: Call) => (
    <TouchableOpacity 
      key={call.id} 
      style={styles.callCard}
      onPress={() => router.push(`/call/${call.id}`)}
    >
      <View style={styles.header}>
        <Text style={styles.caller}>{call.callerNumber}</Text>
        <Badge 
          label={call.finalRiskLevel || 'UNKNOWN'} 
          variant={call.finalRiskLevel === 'HIGH' ? 'danger' : call.finalRiskLevel === 'CAUTION' ? 'warning' : 'success'} 
        />
      </View>
      <View style={styles.details}>
        <Text style={styles.detailText}>Peak Risk: {call.maxRiskScore.toFixed(0)}</Text>
        <Text style={styles.detailText}>Duration: {call.duration}s</Text>
        <Text style={styles.detailText}>Status: {call.status}</Text>
      </View>
      <Text style={styles.timestamp}>{new Date(call.startedAt).toLocaleString()}</Text>
    </TouchableOpacity>
  );

  return (
    <ScreenContainer safeArea={false}>
      <ScrollView contentContainerStyle={styles.container}>
        {calls.map(renderCall)}
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
  callCard: {
    backgroundColor: colors.surface,
    padding: 16,
    borderRadius: 12,
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
