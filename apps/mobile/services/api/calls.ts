import { apiClient } from './client';
import { Call, RiskUpdate } from '../../types';

export const callApi = {
  createCall: (callerNumber: string) => 
    apiClient.post<Call>('/calls', { caller_number: callerNumber }),
    
  getCall: (id: string) => 
    apiClient.get<Call>(`/calls/${id}`),
    
  getCalls: (limit = 20, offset = 0, riskLevel = 'ALL') => 
    apiClient.get<Call[]>(`/calls?limit=${limit}&offset=${offset}&risk_level=${riskLevel}`),
};
