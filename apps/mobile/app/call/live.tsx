import React, { useEffect } from 'react';
import { View, StyleSheet, Text, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button, RiskIndicator, SignalIndicator, Card } from '../../components';
import { colors } from '../../theme/colors';
import { useCallStore } from '../../stores/useCallStore';
import { useLiveCallStore } from '../../stores/liveCallStore';

export default function LiveProtectionScreen() {
  const router = useRouter();
  const activeCall = useCallStore(state => state.activeCall);
  const endCall = useCallStore(state => state.endCall);

  const { connect, disconnect, connectionState, isStale, currentRisk } = useLiveCallStore();

  useEffect(() => {
    if (activeCall) {
      connect(activeCall.id);
    }
    return () => {
      disconnect();
    };
  }, [activeCall]);

  if (!activeCall || !currentRisk) {
    return (
      <ScreenContainer style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.title}>
            {connectionState === 'CONNECTING' ? 'Connecting to VoiceGuard...' : 'Waiting for call data...'}
          </Text>
        </View>
        <View style={styles.actions}>
          <Button title="Go Back" onPress={() => router.back()} />
        </View>
      </ScreenContainer>
    );
  }

  const handleEndCall = () => {
    disconnect();
    endCall();
    router.back();
  };

  const isHighRisk = currentRisk.analysisStatus === 'HIGH';

  const getConnectionColor = () => {
    switch(connectionState) {
      case 'LIVE': return colors.success;
      case 'RECONNECTING': return colors.warning;
      case 'DISCONNECTED': return colors.danger;
      default: return colors.textMuted;
    }
  };

  return (
    <ScreenContainer style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.headerRow}>
          <View style={[styles.statusDot, { backgroundColor: getConnectionColor() }]} />
          <Text style={styles.connectionText}>{connectionState}</Text>
        </View>

        <Text style={styles.title}>VOICEGUARD PROTECTION LIVE</Text>
        <Text style={styles.caller}>Caller: {activeCall.callerNumber}</Text>

        <View style={[styles.contentArea, isStale && styles.staleContent]}>
          {isStale && (
            <View style={styles.staleWarning}>
              <Text style={styles.staleWarningText}>Connection lost. Data may be stale.</Text>
            </View>
          )}
          
          <View style={styles.statusBox}>
            <Text style={styles.statusLabel}>Analysis Status: <Text style={styles.statusValue}>{currentRisk.analysisStatus}</Text></Text>
            <Text style={styles.statusLabel}>Usable Speech: <Text style={styles.statusValue}>{currentRisk.usableSpeechDuration}s</Text></Text>
            <Text style={styles.statusLabel}>Updated At: <Text style={styles.statusValue}>{new Date(currentRisk.updatedAt).toLocaleTimeString()}</Text></Text>
          </View>

          <Card style={styles.riskCard}>
            <Text style={styles.cardHeader}>VOICE INTEGRITY RISK</Text>
            <RiskIndicator score={currentRisk.rollingRiskScore} />
            
            <View style={styles.legend}>
              <Text style={styles.legendText}>0-39 LOW</Text>
              <Text style={styles.legendText}>40-69 CAUTION</Text>
              <Text style={styles.legendText}>70-100 HIGH</Text>
            </View>
          </Card>

          {isHighRisk && (
            <View style={styles.alertBox}>
              <Text style={styles.alertText}>
                Elevated voice-integrity risk detected.{"\n"}Verify the caller using a trusted secondary channel before taking sensitive actions.
              </Text>
            </View>
          )}

          <Card style={styles.signalsCard}>
            <SignalIndicator label="Anti-Spoof" status={currentRisk.antiSpoofSignal} />
            <SignalIndicator label="Speaker Consistency" status={currentRisk.speakerConsistency} />
            <SignalIndicator label="Signal Anomaly" status={currentRisk.signalAnomaly === 'detected' ? 'danger' : currentRisk.signalAnomaly === 'none' ? 'safe' : 'unknown'} />
            <SignalIndicator label="Audio Quality" status={currentRisk.audioQuality} />
          </Card>
        </View>
      </ScrollView>

      <View style={styles.actions}>
        {isHighRisk && (
          <Button 
            title="Start Verification" 
            variant="warning" 
            onPress={() => router.push('/verification')} 
            style={styles.actionBtn}
          />
        )}
        <Button 
          title="Acknowledge & Back" 
          variant="secondary" 
          onPress={handleEndCall} 
          style={styles.actionBtn}
        />
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scroll: {
    padding: 16,
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  connectionText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.textMuted,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.primary,
    textAlign: 'center',
  },
  caller: {
    fontSize: 18,
    color: colors.text,
    textAlign: 'center',
    marginBottom: 8,
    fontWeight: '600',
  },
  contentArea: {
    gap: 16,
  },
  staleContent: {
    opacity: 0.6,
  },
  staleWarning: {
    backgroundColor: colors.warning,
    padding: 8,
    borderRadius: 4,
    alignItems: 'center',
  },
  staleWarningText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 12,
  },
  statusBox: {
    backgroundColor: colors.surface,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statusLabel: {
    color: colors.textMuted,
    fontSize: 14,
    marginBottom: 4,
  },
  statusValue: {
    color: colors.text,
    fontWeight: 'bold',
  },
  riskCard: {
    paddingVertical: 20,
  },
  cardHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  legendText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  alertBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: colors.danger,
  },
  alertText: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  signalsCard: {
    gap: 0,
  },
  actions: {
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.background,
  },
  actionBtn: {
    width: '100%',
  }
});
