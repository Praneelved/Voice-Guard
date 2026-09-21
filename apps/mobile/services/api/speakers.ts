import { apiClient } from './client';
import { TrustedVoice } from '../../types';

export const speakerApi = {
  getSpeakers: () => 
    apiClient.get<TrustedVoice[]>('/speakers'),
    
  getModels: () => 
    apiClient.get<{ models: any[] }>('/models'),
};
