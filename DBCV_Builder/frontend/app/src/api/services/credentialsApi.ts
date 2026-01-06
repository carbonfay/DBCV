import apiClient, { safeApiCall } from '@/api/axios';

const credentialsApi = {
  readCredentials(botId: string, params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get(`/bots/${botId}/credentials/`, { params }));
  },
  
  createCredential(botId: string, credentialData: Record<string, unknown>) {
    return safeApiCall(apiClient.post(`/bots/${botId}/credentials/`, credentialData));
  },
  
  readCredential(botId: string, credId: string) {
    return safeApiCall(apiClient.get(`/bots/${botId}/credentials/${credId}`));
  },
  
  updateCredential(botId: string, credId: string, credentialData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/bots/${botId}/credentials/${credId}`, credentialData));
  },
  
  deleteCredential(botId: string, credId: string) {
    return safeApiCall(apiClient.delete(`/bots/${botId}/credentials/${credId}`));
  },
  
  makeDefaultCredential(botId: string, credId: string) {
    return safeApiCall(apiClient.post(`/bots/${botId}/credentials/${credId}/make-default`));
  },
  
  getProviders() {
    return safeApiCall(apiClient.get('/credentials/providers'));
  },
  
  getStrategies(provider?: string) {
    const params = provider ? { provider } : {};
    return safeApiCall(apiClient.get('/credentials/strategies', { params }));
  },
};

export default credentialsApi;
