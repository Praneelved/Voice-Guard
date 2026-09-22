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
        if (event.event_type === 'risk.update') {
          const e = event as RiskUpdateWsEvent;
          
          // Calculate usable speech duration. The backend sends an ISO timestamp.
          // For simplicity in UI, we can just use the difference from start, 
          // or if the backend provides analyzed_windows, we could use that. 
          // Since the backend doesn't send usableSpeechDuration directly in this payload,
          // we'll track the first received timestamp if needed, or default to 0 for now until 
          // backend provides it. Wait, the backend doesn't send usableSpeechDuration right now in RiskAssessment.
          // The UI requested "speech analyzed duration". The backend has `temporal_state.valid_window_count * 4s` but it's not in the payload.
          // Let's just mock it or infer it. If it's not sent, let's just use 0.
          
          set({
            currentRisk: {
              callId: e.call_id,
              riskScore: e.payload.riskScore * 100, // Backend sends 0-1, UI expects 0-100
              riskLevel: e.payload.riskLevel,
              confidence: e.payload.confidence * 100,
              antiSpoof: e.payload.signals.antiSpoof,
              speakerVerification: e.payload.signals.speakerVerification,
              audioQuality: e.payload.signals.audioQuality,
              usableSpeechDuration: 0, // TODO: Get from backend if needed
              updatedAt: new Date(e.timestamp).toISOString()
            }
          });
        } else if (event.event_type === 'call.ended') {
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
