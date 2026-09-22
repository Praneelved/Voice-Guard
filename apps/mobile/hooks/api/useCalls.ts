import { useQuery } from '@tanstack/react-query';
import { callApi } from '../../services/api/calls';
import { mockCalls } from '../../services/mockDataService';
import { CONFIG } from '../../constants/config';

export const useCalls = (riskLevel: string = 'ALL') => {
  return useQuery({
    queryKey: ['calls', riskLevel],
    queryFn: async () => {
      if (CONFIG.USE_MOCKS) {
        await new Promise(resolve => setTimeout(resolve, 500));
        let data = mockCalls;
        if (riskLevel !== 'ALL') {
          data = data.filter(c => c.finalRiskLevel === riskLevel);
        }
        return data;
      }
      return callApi.getCalls(50, 0, riskLevel); // Fetch up to 50 for now, flatlist can do pagination later
    },
    retry: 2,
  });
};
