import { useQuery } from '@tanstack/react-query';
import { speakerApi } from '../../services/api/speakers';
import { mockTrustedVoices } from '../../services/mockDataService';
import { CONFIG } from '../../constants/config';

export const useSpeakers = () => {
  return useQuery({
    queryKey: ['speakers'],
    queryFn: async () => {
      if (CONFIG.USE_MOCKS) {
        await new Promise(resolve => setTimeout(resolve, 500));
        return mockTrustedVoices;
      }
      return speakerApi.getSpeakers();
    },
    retry: 2,
  });
};
