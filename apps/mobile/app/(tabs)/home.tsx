import React from 'react';
import { View, StyleSheet, ScrollView, Text, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Card, Button, SignalIndicator, ErrorState } from '../../components';
import { colors } from '../../theme/colors';
import { useAuthStore } from '../../stores/useAuthStore';
import { useCallStore } from '../../stores/useCallStore';
import { useLiveCallStore } from '../../stores/liveCallStore';
import { mockActiveCall } from '../../services/mockDataService';
import { CONFIG } from '../../constants/config';
import { useAlerts } from '../../hooks/api/useAlerts';
import { useCalls } from '../../hooks/api/useCalls';
import { useSpeakers } from '../../hooks/api/useSpeakers';

export default function HomeScreen() {
  const router = useRouter();
  const activeCall = useCallStore(state => state.activeCall);
  const currentRisk = useLiveCallStore(state => state.currentRisk);
  const setActiveCall = useCallStore(state => state.setActiveCall);

  const { data: alerts, isLoading: loadingAlerts, error: errorAlerts, refetch: refetchAlerts } = useAlerts();
  const { data: calls, isLoading: loadingCalls, error: errorCalls, refetch: refetchCalls } = useCalls();
  const { data: speakers, isLoading: loadingSpeakers, error: errorSpeakers, refetch: refetchSpeakers } = useSpeakers();

  const startMockCall = () => {
    setActiveCall(mockActiveCall);
    router.push('/call/live');
  };

  const isLoading = loadingAlerts || loadingCalls || loadingSpeakers;
  const isError = errorAlerts || errorCalls || errorSpeakers;

  const handleRetry = () => {
    if (errorAlerts) refetchAlerts();
    if (errorCalls) refetchCalls();
    if (errorSpeakers) refetchSpeakers();
  };

  if (isError) {
    return (
      <ScreenContainer safeArea={false}>
        <ErrorState 
          title="Connection Error" 
          message="Failed to load dashboard data. You might be offline." 
          onRetry={handleRetry} 
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer safeArea={false}>
      <ScrollView contentContainerStyle={styles.container}>
        
        <View style={styles.header}>
          <Text style={styles.title}>VoiceGuard</Text>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Protection Status: Active</Text>
          </View>
        </View>

        <Card style={styles.card}>
          <Text style={styles.cardTitle}>System Status</Text>
          <SignalIndicator label="VoiceGuard Online" status="safe" />
          <SignalIndicator label="Realtime Protection Ready" status="safe" />
        </Card>

        {activeCall ? (
          <Card style={[styles.card, styles.activeCallCard]}>
            <Text style={styles.cardTitle}>Active Protected Call</Text>
            <Text style={styles.caller}>{activeCall.callerNumber}</Text>
            <Text style={styles.info}>Duration: {currentRisk?.usableSpeechDuration || 0}s</Text>
            <Text style={styles.info}>Current Risk: {currentRisk?.rollingRiskScore.toFixed(1) || 0}</Text>
            <Button 
              title="View Live Protection" 
              onPress={() => router.push('/call/live')} 
              style={{marginTop: 12}}
            />
          </Card>
        ) : CONFIG.USE_MOCKS ? (
          <Card style={styles.card}>
            <Text style={styles.cardTitle}>Simulate Incoming Call</Text>
            <Button 
              title="Start Mock Call" 
              onPress={startMockCall} 
            />
          </Card>
        ) : null}

        <Card style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardTitle}>Recent Activity</Text>
            {isLoading && <ActivityIndicator size="small" color={colors.primary} />}
          </View>
          <View style={styles.activityRow}>
            <Text style={styles.activityLabel}>Recent Alerts:</Text>
            <Text style={styles.activityValue}>{alerts?.length || 0}</Text>
          </View>
          <View style={styles.activityRow}>
            <Text style={styles.activityLabel}>Recent Calls:</Text>
            <Text style={styles.activityValue}>{calls?.length || 0}</Text>
          </View>
          <View style={styles.activityRow}>
            <Text style={styles.activityLabel}>Trusted Voices Enrolled:</Text>
            <Text style={styles.activityValue}>{speakers?.length || 0}</Text>
          </View>
        </Card>

      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 16,
  },
  header: {
    marginBottom: 8,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.primary,
    marginBottom: 4,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.success,
  },
  statusText: {
    fontSize: 16,
    color: colors.text,
    fontWeight: '600',
  },
  card: {
    gap: 12,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  activeCallCard: {
    borderColor: colors.warning,
    borderWidth: 2,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  caller: {
    fontSize: 22,
    color: colors.text,
    fontWeight: 'bold',
  },
  info: {
    color: colors.textMuted,
    fontSize: 14,
  },
  activityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  activityLabel: {
    color: colors.text,
    fontSize: 16,
  },
  activityValue: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
  },
});
