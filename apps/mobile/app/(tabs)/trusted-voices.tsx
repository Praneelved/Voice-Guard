import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer, EmptyState, Button, Badge, Loading } from '../../components';
import { useSpeakers } from '../../hooks/api/useSpeakers';
import { colors } from '../../theme/colors';
import { TrustedVoice } from '../../types';

export default function TrustedVoicesScreen() {
  const router = useRouter();
  const { data: voices, isLoading } = useSpeakers();

  const renderVoice = (voice: TrustedVoice) => (
    <View key={voice.id} style={styles.voiceCard}>
      <View style={styles.header}>
        <Text style={styles.name}>{voice.name}</Text>
        <Badge 
          label={voice.status === 'active' ? 'Active' : 'Needs Re-enrollment'} 
          variant={voice.status === 'active' ? 'success' : 'warning'} 
        />
      </View>
      <Text style={styles.timestamp}>Enrolled: {new Date(voice.enrolledAt).toLocaleDateString()}</Text>
      
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionLink} onPress={() => {}}>
          <Text style={styles.actionText}>View</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionLink} onPress={() => router.push('/enrollment')}>
          <Text style={styles.actionText}>Re-enroll</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionLink} onPress={() => {}}>
          <Text style={[styles.actionText, { color: colors.danger }]}>Remove</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <ScreenContainer safeArea={false}>
      <ScrollView contentContainerStyle={styles.container}>
        <Button 
          title="Add Trusted Voice" 
          onPress={() => router.push('/enrollment')} 
          style={styles.addBtn}
        />
        
        {isLoading ? (
          <Loading size="large" />
        ) : !voices || voices.length === 0 ? (
          <EmptyState 
            title="No Trusted Voices" 
            message="Enroll voices of family and coworkers to verify their identity on calls."
          />
        ) : (
          voices.map(renderVoice)
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 16,
  },
  addBtn: {
    marginBottom: 8,
  },
  voiceCard: {
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
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
  },
  timestamp: {
    color: colors.textMuted,
    fontSize: 14,
    marginBottom: 16,
  },
  actions: {
    flexDirection: 'row',
    gap: 16,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 12,
  },
  actionLink: {
    paddingVertical: 4,
  },
  actionText: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: 14,
  }
});
