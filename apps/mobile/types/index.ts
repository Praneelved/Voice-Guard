export interface User {
  id: string;
  email: string;
  name: string;
  organizationId?: string;
}

export type CallStatus = 'active' | 'completed' | 'failed';
export type RiskLevel = 'LOW' | 'CAUTION' | 'HIGH' | 'INSUFFICIENT_EVIDENCE' | 'ANALYSIS_UNAVAILABLE' | 'STARTING' | 'ANALYZING';

export interface Call {
  id: string;
  providerCallId: string;
  callerNumber: string;
  startedAt: string;
  endedAt?: string;
  duration?: number; // seconds
  status: CallStatus;
  maxRiskScore: number;
  finalRiskLevel?: RiskLevel;
}

export interface RiskUpdate {
  callId: string;
  rollingRiskScore: number; // 0-100
  analysisStatus: RiskLevel;
  antiSpoofSignal: 'safe' | 'warning' | 'danger' | 'unknown';
  speakerConsistency: 'verifying' | 'verified' | 'mismatch' | 'unknown';
  signalAnomaly: 'none' | 'detected' | 'unknown';
  audioQuality: 'good' | 'poor' | 'unknown';
  usableSpeechDuration: number; // seconds
  updatedAt: string;
}

export interface Alert {
  id: string;
  callId: string;
  callerNumber: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  riskLevel: RiskLevel;
  verificationStatus: 'pending' | 'verified' | 'failed' | 'none';
}

export interface TrustedVoice {
  id: string;
  name: string;
  enrolledAt: string;
  status: 'active' | 'pending_re-enrollment';
}

export type ConnectionState = 'CONNECTING' | 'LIVE' | 'RECONNECTING' | 'DISCONNECTED';

export interface BaseWsEvent {
  type: string;
  timestamp_ms: number;
  call_id: string;
}

export interface RiskUpdateWsEvent extends BaseWsEvent {
  type: 'risk.update';
  risk: number; // 0-1
  level: RiskLevel;
  confidence: number;
  quality: 'good' | 'poor' | 'unknown';
  signals: {
    antispoof: number;
    speaker_mismatch: number | null;
    signal_anomaly: number | null;
  };
}

export interface WsEvent extends BaseWsEvent {
  type: 'call.started' | 'risk.update' | 'risk.alert' | 'analysis.insufficient' | 'analysis.unavailable' | 'verification.requested' | 'verification.completed' | 'call.ended';
  [key: string]: any;
}

