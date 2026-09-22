import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Text, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, Button, RiskIndicator, Card } from '../../components';
import { colors } from '../../theme/colors';
import { useCallStore } from '../../stores/useCallStore';
import { useLiveCallStore } from '../../stores/liveCallStore';

export default function LiveProtectionScreen() {
  const router = useRouter();
  const activeCall = useCallStore(state => state.activeCall);
  const endCall = useCallStore(state => state.endCall);

  const { connect, disconnect, connectionState, isStale, currentRisk } = useLiveCallStore();
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [speechAnalyzedSeconds, setSpeechAnalyzedSeconds] = useState(0);

  useEffect(() => {
    if (activeCall) {
      connect(activeCall.id);
    }
    return () => {
      disconnect();
    };
  }, [activeCall, connect, disconnect]);

  useEffect(() => {
    // Basic approximation of speech analyzed duration
    if (currentRisk && currentRisk.riskLevel !== 'STARTING') {
      setSpeechAnalyzedSeconds(prev => prev + 4); // assume ~4 seconds per event roughly
    }
  }, [currentRisk?.updatedAt]);

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

  const getSignalStatusColor = (status: string) => {
    switch (status) {
      case 'SAFE':
      case 'GOOD':
      case 'VERIFIED':
        return colors.success;
      case 'WARNING':
      case 'CAUTION':
      case 'MEDIUM':
        return colors.warning;
      case 'DANGER':
      case 'HIGH':
      case 'MISMATCH':
        return colors.danger;
      default:
        return colors.textMuted;
    }
  };

  const getSpeakerText = () => {
    if (!currentRisk.speakerVerification.available) return "Not enrolled";
    return currentRisk.speakerVerification.similarity! > 0.5 ? "Verified" : "Mismatch detected";
  };

  const isHighRisk = currentRisk.riskLevel === 'HIGH';

  return (
    <ScreenContainer style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.headerRow}>
          <View style={[styles.statusDot, { backgroundColor: getConnectionColor() }]} />
          <Text style={styles.connectionText}>{connectionState}</Text>
        </View>

        <Text style={styles.title}>VoiceGuard Live Protection</Text>
        <Text style={styles.caller}>Caller: {activeCall.callerNumber}</Text>

        <View style={[styles.contentArea, isStale && styles.staleContent]}>
          {isStale && (
            <View style={styles.staleWarning}>
              <Text style={styles.staleWarningText}>Connection lost. Data may be stale.</Text>
            </View>
          )}
          
          <Card style={styles.riskCard}>
            <Text style={styles.cardHeader}>Voice Authenticity Risk</Text>
            <RiskIndicator score={currentRisk.riskScore} />
            <Text style={[styles.riskLevelText, { color: getSignalStatusColor(currentRisk.riskLevel) }]}>
              {currentRisk.riskLevel}
            </Text>
            
            <View style={styles.statsRow}>
              <Text style={styles.statText}>Evidence confidence: {Math.round(currentRisk.confidence)}%</Text>
              <Text style={styles.statText}>Speech analyzed: {speechAnalyzedSeconds} seconds</Text>
            </View>
          </Card>

          {isHighRisk && (
            <View style={styles.alertBox}>
              <Text style={styles.alertText}>
                Potential synthetic or impersonated voice characteristics were detected.{"\n\n"}
                Verify the caller through another trusted channel before sharing credentials, OTPs, confidential information, or authorizing sensitive actions.
              </Text>
            </View>
          )}

          <Card style={styles.signalsCard}>
            <Text style={styles.cardHeader}>Signals</Text>
            
            <View style={styles.signalRow}>
              <Text style={styles.signalLabel}>Synthetic Speech Indicators</Text>
              <Text style={[styles.signalValue, { color: getSignalStatusColor(currentRisk.antiSpoof.status) }]}>
                {currentRisk.antiSpoof.status.replace(/_/g, ' ')}
              </Text>
            </View>

            <View style={styles.signalRow}>
              <Text style={styles.signalLabel}>Trusted Speaker</Text>
              <Text style={[styles.signalValue, { color: getSignalStatusColor(getSpeakerText().toUpperCase()) }]}>
                {getSpeakerText()}
              </Text>
            </View>

            <View style={styles.signalRow}>
              <Text style={styles.signalLabel}>Audio Quality</Text>
              <Text style={[styles.signalValue, { color: getSignalStatusColor(currentRisk.audioQuality.status) }]}>
                {currentRisk.audioQuality.status}
              </Text>
            </View>
          </Card>

          <TouchableOpacity 
            style={styles.techDetailsToggle} 
            onPress={() => setShowTechnicalDetails(!showTechnicalDetails)}
          >
            <Text style={styles.techDetailsText}>
              {showTechnicalDetails ? "▼ Hide Technical Details" : "▶ Show Technical Details"}
            </Text>
          </TouchableOpacity>

          {showTechnicalDetails && (
            <Card style={styles.techCard}>
              <Text style={styles.techRow}>Raw Anti-Spoof Score: {currentRisk.antiSpoof.score ? currentRisk.antiSpoof.score.toFixed(4) : 'N/A'}</Text>
              <Text style={styles.techRow}>Speaker Similarity: {currentRisk.speakerVerification.similarity ? currentRisk.speakerVerification.similarity.toFixed(4) : 'N/A'}</Text>
              <Text style={styles.techRow}>Model Version: AASIST v1.0 / ECAPA-TDNN</Text>
              <Text style={styles.techRow}>Last Updated: {new Date(currentRisk.updatedAt).toLocaleTimeString()}</Text>
            </Card>
          )}
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
    alignItems: 'center',
  },
  riskLevelText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statsRow: {
    marginTop: 16,
    alignItems: 'center',
  },
  statText: {
    color: colors.textMuted,
    fontSize: 14,
    marginBottom: 4,
  },
  cardHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 16,
    textAlign: 'center',
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
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
  signalsCard: {
    gap: 12,
  },
  signalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  signalLabel: {
    fontSize: 16,
    color: colors.text,
  },
  signalValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  techDetailsToggle: {
    padding: 12,
    alignItems: 'center',
  },
  techDetailsText: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  techCard: {
    backgroundColor: '#1E293B',
    padding: 16,
    gap: 8,
  },
  techRow: {
    fontFamily: 'monospace',
    color: '#94A3B8',
    fontSize: 12,
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
