import { apiClient } from './client';

export const verificationApi = {
  startVerification: (callId: string) => 
    apiClient.post<{ status: string; call_id: string; challenge: string; expires_in: number }>(`/verification/${callId}`),
};
