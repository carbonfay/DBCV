import apiClient, { safeApiCall } from '@/api/axios';

const integrationsApi = {
  getCatalog(params: { category?: string; latest_only?: boolean } = {}) {
    return safeApiCall(apiClient.get('/integrations/catalog', { params }));
  },

  getMetadata(integrationId: string, version?: string) {
    const params = version ? { version } : {};
    return safeApiCall(apiClient.get(`/integrations/${integrationId}/metadata`, { params }));
  },
};

export default integrationsApi;

