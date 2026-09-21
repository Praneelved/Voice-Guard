import { apiClient } from './client';
import { Call, RiskUpdate } from '../../types';

export const callApi = {
  createCall: (callerNumber: string) => 
    apiClient.post<Call>('/calls', { caller_number: callerNumber }),
    
  getCall: (id: string) => 
    apiClient.get<Call>(`/calls/${id}`),
    
  getCalls: () => 
    apiClient.get<Call[]>('/calls'),
    
  getCallEvents: (id: string) => 
    apiClient.get<{ events: RiskUpdate[] }>(`/calls/${id}/events`),
};
