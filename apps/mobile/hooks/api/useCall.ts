import { useQuery } from '@tanstack/react-query';
import { callApi } from '../../services/api/calls';
import { CONFIG } from '../../constants/config';
import { mockCalls } from '../../services/mockDataService';

export const useCall = (id: string) => {
  return useQuery({
    queryKey: ['call', id],
    queryFn: async () => {
      if (CONFIG.USE_MOCKS) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const call = mockCalls.find(c => c.id === id);
        if (call) {
          return {
            ...call,
            timeline: [
              { timestamp: call.startedAt, description: "Call started" },
              { timestamp: new Date(new Date(call.startedAt).getTime() + 4000).toISOString(), description: "Sufficient speech collected" },
              { timestamp: new Date(new Date(call.startedAt).getTime() + 8000).toISOString(), description: "Risk LOW 18%", risk_level: "LOW", risk_score: 18 },
              { timestamp: new Date(new Date(call.startedAt).getTime() + 16000).toISOString(), description: "Risk MEDIUM 53%", risk_level: "MEDIUM", risk_score: 53 },
              { timestamp: new Date(new Date(call.startedAt).getTime() + 27000).toISOString(), description: "HIGH risk alert issued", risk_level: "HIGH" },
              { timestamp: call.endedAt || new Date().toISOString(), description: "Call ended" },
            ]
          };
        }
        throw new Error("Mock call not found");
      }
      return callApi.getCall(id);
    },
    enabled: !!id,
    retry: 1,
  });
};
