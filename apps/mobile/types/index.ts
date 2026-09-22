export interface User {
  id: string;
  email: string;
  name: string;
  organizationId?: string;
}

export type CallStatus = 'active' | 'completed' | 'failed';
export type RiskLevel = 'LOW' | 'CAUTION' | 'HIGH' | 'INSUFFICIENT_EVIDENCE' | 'ANALYSIS_UNAVAILABLE' | 'STARTING' | 'ANALYZING';

export interface CallEvent {
  timestamp: string;
  description: string;
  risk_level?: RiskLevel | string;
  risk_score?: number;
}

export interface Call {
  id: string;
  providerCallId?: string; // It was mapped to callerNumber but let's keep optional if needed
  callerNumber: string;
  startedAt: string;
  endedAt?: string;
  duration?: number; // seconds
  status: CallStatus;
  maxRiskScore: number;
  finalRiskLevel?: RiskLevel;
  analyzedDuration?: number;
  timeline?: CallEvent[];
}

export interface RiskUpdate {
  callId: string;
  riskScore: number;
  riskLevel: RiskLevel;
  confidence: number;
  usableSpeechDuration: number;
  
  antiSpoof: {
    status: string;
    score: number | null;
    confidence: number | null;
  };
  speakerVerification: {
    available: boolean;
    similarity: number | null;
  };
  audioQuality: {
    status: string;
  };
  
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
  event_type: string;
  timestamp: string;
  call_id: string;
  session_id: string;
}

export interface RiskUpdateWsEvent extends BaseWsEvent {
  event_type: 'risk.update';
  payload: {
    riskScore: number;
    riskLevel: RiskLevel;
    confidence: number;
    signals: {
      antiSpoof: {
        status: string;
        score: number | null;
        confidence: number | null;
      };
      speakerVerification: {
        available: boolean;
        similarity: number | null;
      };
      audioQuality: {
        status: string;
      };
    };
    evidence: Array<{ code: string; severity: string }>;
  };
}

export interface WsEvent extends BaseWsEvent {
  event_type: 'call.started' | 'risk.update' | 'risk.alert' | 'analysis.insufficient' | 'analysis.unavailable' | 'verification.requested' | 'verification.completed' | 'call.ended';
  payload: any;
}

