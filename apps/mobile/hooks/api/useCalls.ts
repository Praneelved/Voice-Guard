import { useQuery } from '@tanstack/react-query';
import { callApi } from '../../services/api/calls';
import { mockCalls } from '../../services/mockDataService';
import { CONFIG } from '../../constants/config';

export const useCalls = () => {
  return useQuery({
    queryKey: ['calls'],
    queryFn: async () => {
      if (CONFIG.USE_MOCKS) {
        await new Promise(resolve => setTimeout(resolve, 500));
        return mockCalls;
      }
      return callApi.getCalls();
    },
    retry: 2,
  });
};
