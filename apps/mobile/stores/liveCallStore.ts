import { create } from 'zustand';
import { ConnectionState, RiskUpdate, RiskUpdateWsEvent } from '../types';
import { CallWebSocketClient } from '../services/websocket/callEvents';

interface LiveCallState {
  connectionState: ConnectionState;
  isStale: boolean;
  currentRisk: RiskUpdate | null;
  wsClient: CallWebSocketClient | null;
  connect: (callId: string) => void;
  disconnect: () => void;
}

export const useLiveCallStore = create<LiveCallState>((set, get) => ({
  connectionState: 'DISCONNECTED',
  isStale: true,
  currentRisk: null,
  wsClient: null,
  
  connect: (callId: string) => {
    // Clean up any existing connection first
    get().disconnect();
    
    const client = new CallWebSocketClient(
      (event) => {
        if (event.type === 'risk.update') {
          const e = event as RiskUpdateWsEvent;
          set({
            currentRisk: {
              callId: e.call_id,
              rollingRiskScore: e.risk * 100, // Backend sends 0-1, UI expects 0-100
              analysisStatus: e.level,
              antiSpoofSignal: e.signals.antispoof > 0.5 ? 'safe' : e.signals.antispoof > 0.2 ? 'warning' : 'danger',
              speakerConsistency: e.signals.speaker_mismatch === null ? 'unknown' : e.signals.speaker_mismatch > 0.5 ? 'mismatch' : 'verified',
              signalAnomaly: e.signals.signal_anomaly === null ? 'unknown' : e.signals.signal_anomaly > 0.5 ? 'detected' : 'none',
              audioQuality: e.quality,
              usableSpeechDuration: Math.floor(e.timestamp_ms / 1000), // convert ms to seconds
              updatedAt: new Date().toISOString()
            }
          });
        } else if (event.type === 'call.ended') {
          get().disconnect();
        }
      },
      (state) => {
        set({
          connectionState: state,
          // It's considered stale if it's not live (e.g. disconnected or currently reconnecting)
          isStale: state !== 'LIVE'
        });
      }
    );

    client.connect(callId);
    set({ wsClient: client });
  },

  disconnect: () => {
    const { wsClient } = get();
    if (wsClient) {
      wsClient.disconnect();
    }
    set({ wsClient: null, connectionState: 'DISCONNECTED', isStale: true });
  }
}));
