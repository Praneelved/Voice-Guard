import React from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ScreenContainer, Button, Badge, Card, ErrorState } from '../../components';
import { colors } from '../../theme/colors';
import { useCall } from '../../hooks/api/useCall';

export default function CallDetailsScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  
  const { data: call, isLoading, error, refetch } = useCall(id as string);

  if (error) {
    return (
      <ScreenContainer safeArea={false}>
        <ErrorState 
          title="Failed to Load Call" 
          message="We couldn't connect to the server." 
          onRetry={refetch} 
        />
        <Button title="Go Back" onPress={() => router.back()} style={styles.backBtn} />
      </ScreenContainer>
    );
  }

  if (isLoading || !call) {
    return (
      <ScreenContainer safeArea={false} style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </ScreenContainer>
    );
  }

  // Format time relative to call start
  const formatTimeDiff = (startStr: string, currentStr: string) => {
    const start = new Date(startStr).getTime();
    const current = new Date(currentStr).getTime();
    const diffSeconds = Math.floor((current - start) / 1000);
    
    if (diffSeconds < 0) return "00:00"; // Safeguard
    
    const minutes = Math.floor(diffSeconds / 60);
    const seconds = diffSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getTimelineDotColor = (level?: string) => {
    switch(level) {
      case 'HIGH':
      case 'critical':
      case 'danger':
        return colors.danger;
      case 'MEDIUM':
      case 'warning':
      case 'CAUTION':
        return colors.warning;
      case 'LOW':
      case 'success':
        return colors.success;
      default:
        return colors.primary;
    }
  };

  return (
    <ScreenContainer safeArea={false}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Card style={styles.summaryCard}>
          <Text style={styles.caller}>{call.callerNumber}</Text>
          <Text style={styles.subText}>{new Date(call.startedAt).toLocaleString()}</Text>
          
          <View style={styles.statsRow}>
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>Risk</Text>
              <Badge 
                label={call.finalRiskLevel || 'UNKNOWN'} 
                variant={call.finalRiskLevel === 'HIGH' ? 'danger' : call.finalRiskLevel === 'CAUTION' || call.finalRiskLevel === 'MEDIUM' ? 'warning' : 'success'} 
              />
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>Peak Score</Text>
              <Text style={styles.statValue}>{call.maxRiskScore.toFixed(0)}%</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>Duration</Text>
              <Text style={styles.statValue}>{call.duration || 0}s</Text>
            </View>
          </View>
        </Card>

        <Text style={styles.timelineHeader}>Evidence Timeline</Text>
        
        <View style={styles.timeline}>
          {call.timeline?.map((event, index) => {
            const isLast = index === call.timeline!.length - 1;
            const timeDiff = formatTimeDiff(call.startedAt, event.timestamp);
            
            return (
              <View key={index} style={styles.timelineEvent}>
                <View style={styles.timelineLeft}>
                  <Text style={styles.timeText}>{timeDiff}</Text>
                </View>
                
                <View style={styles.timelineCenter}>
                  <View style={[styles.timelineDot, { backgroundColor: getTimelineDotColor(event.risk_level) }]} />
                  {!isLast && <View style={styles.timelineLine} />}
                </View>
                
                <View style={styles.timelineRight}>
                  <Text style={styles.eventDesc}>{event.description}</Text>
                </View>
              </View>
            );
          })}
          
          {(!call.timeline || call.timeline.length === 0) && (
            <Text style={styles.noEventsText}>No timeline events available.</Text>
          )}
        </View>

        <Button title="Go Back" onPress={() => router.back()} style={styles.btn} variant="secondary" />
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  center: {
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  scroll: {
    padding: 16,
    gap: 16,
  },
  summaryCard: {
    alignItems: 'center',
    paddingTop: 24,
    paddingBottom: 24,
  },
  caller: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  subText: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  statBox: {
    alignItems: 'center',
    gap: 8,
  },
  statLabel: {
    color: colors.textMuted,
    fontSize: 12,
  },
  statValue: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
  },
  timelineHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 8,
    marginBottom: 8,
  },
  timeline: {
    paddingLeft: 8,
    paddingBottom: 16,
  },
  timelineEvent: {
    flexDirection: 'row',
    minHeight: 48,
  },
  timelineLeft: {
    width: 50,
    paddingTop: 2,
  },
  timeText: {
    color: colors.textMuted,
    fontSize: 14,
    fontWeight: '600',
  },
  timelineCenter: {
    width: 24,
    alignItems: 'center',
  },
  timelineDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 4,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: colors.border,
    marginTop: 4,
    marginBottom: 4,
  },
  timelineRight: {
    flex: 1,
    paddingLeft: 12,
    paddingBottom: 24,
  },
  eventDesc: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 22,
  },
  noEventsText: {
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 16,
  },
  backBtn: {
    margin: 16,
  },
  btn: {
    marginTop: 16,
  }
});
