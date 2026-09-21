import { useQuery } from '@tanstack/react-query';
import { alertApi } from '../../services/api/alerts';
import { mockAlerts } from '../../services/mockDataService';
import { CONFIG } from '../../constants/config';

export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      if (CONFIG.USE_MOCKS) {
        // simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500));
        return mockAlerts;
      }
      return alertApi.getAlerts();
    },
    retry: 2,
  });
};
