import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, EmptyState, Badge, ErrorState } from '../../components';
import { colors } from '../../theme/colors';
import { Call } from '../../types';
import { useCalls } from '../../hooks/api/useCalls';

const FILTER_OPTIONS = ['ALL', 'LOW', 'MEDIUM', 'HIGH'];

export default function HistoryScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState('ALL');
  
  const { data: calls, isLoading, error, refetch } = useCalls(filter);

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

  const renderFilter = () => (
    <View style={styles.filterContainer}>
      {FILTER_OPTIONS.map(opt => (
        <TouchableOpacity
          key={opt}
          style={[styles.filterChip, filter === opt && styles.filterChipActive]}
          onPress={() => setFilter(opt)}
        >
          <Text style={[styles.filterText, filter === opt && styles.filterTextActive]}>
            {opt}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  return (
    <ScreenContainer safeArea={false}>
      {renderFilter()}
      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : !calls || calls.length === 0 ? (
        <EmptyState 
          title="No Call History" 
          message={filter === 'ALL' ? "You haven't made any protected calls yet." : `No calls found with ${filter} risk.`}
        />
      ) : (
        <FlatList
          data={calls}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => renderCall(item)}
          contentContainerStyle={styles.container}
          onRefresh={refetch}
          refreshing={isLoading}
          onEndReached={() => {
            // Future implementation: Fetch next page of results
          }}
          onEndReachedThreshold={0.5}
        />
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  center: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 16,
    paddingBottom: 8,
    gap: 8,
  },
  filterChip: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: 'bold',
  },
  filterTextActive: {
    color: '#000',
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
