import { apiClient } from './client';
import { Alert } from '../../types';

export const alertApi = {
  getAlerts: () => 
    apiClient.get<Alert[]>('/alerts'),
    
  acknowledgeAlert: (id: string) => 
    apiClient.post<{ status: string; alert_id: string }>(`/alerts/${id}/ack`),
};
