import { create } from 'zustand';
import { Call, RiskUpdate } from '../types';

interface CallState {
  activeCall: Call | null;
  setActiveCall: (call: Call) => void;
  endCall: () => void;
}

export const useCallStore = create<CallState>((set) => ({
  activeCall: null,
  setActiveCall: (call) => set({ activeCall: call }),
  endCall: () => set({ activeCall: null }),
}));
