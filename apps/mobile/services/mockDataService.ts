import { Call, Alert, TrustedVoice } from '../types';

export const mockCalls: Call[] = [
  {
    id: 'c1',
    providerCallId: 'pc1',
    callerNumber: '+1 (555) 019-8234',
    startedAt: new Date(Date.now() - 3600000).toISOString(),
    endedAt: new Date(Date.now() - 3300000).toISOString(),
    duration: 300,
    status: 'completed',
    maxRiskScore: 24,
    finalRiskLevel: 'LOW',
  },
  {
    id: 'c2',
    providerCallId: 'pc2',
    callerNumber: '+1 (555) 998-1234',
    startedAt: new Date(Date.now() - 86400000).toISOString(),
    endedAt: new Date(Date.now() - 86000000).toISOString(),
    duration: 400,
    status: 'completed',
    maxRiskScore: 82,
    finalRiskLevel: 'HIGH',
  },
];

export const mockAlerts: Alert[] = [
  {
    id: 'a1',
    callId: 'c2',
    callerNumber: '+1 (555) 998-1234',
    severity: 'critical',
    timestamp: new Date(Date.now() - 86100000).toISOString(),
    riskLevel: 'HIGH',
    verificationStatus: 'failed',
  },
];

export const mockTrustedVoices: TrustedVoice[] = [
  {
    id: 'tv1',
    name: 'Sarah (CEO)',
    enrolledAt: new Date(Date.now() - 1000000000).toISOString(),
    status: 'active',
  },
  {
    id: 'tv2',
    name: 'IT Support Team',
    enrolledAt: new Date(Date.now() - 2000000000).toISOString(),
    status: 'active',
  }
];

export const mockActiveCall: Call = {
  id: 'active_1',
  providerCallId: 'pc_active',
  callerNumber: '+1 (555) 112-9988',
  startedAt: new Date().toISOString(),
  status: 'active',
  maxRiskScore: 0,
};
