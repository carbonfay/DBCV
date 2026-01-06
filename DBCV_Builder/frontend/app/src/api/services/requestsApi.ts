import apiClient, { safeApiCall } from '@/api/axios';

const requestsApi = {
  readRequests(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/requests/', { params }));
  },

  createRequest(requestData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/requests/', requestData));
  },

  updateRequest(requestId: string, requestData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/requests/${requestId}`, requestData));
  },

  deleteRequest(requestId: string) {
    return safeApiCall(apiClient.delete(`/requests/${requestId}`));
  },

  executeRequest(requestId: string, variables?: Record<string, unknown>, dryRun?: boolean) {
    const body = {
      variables: variables || {},
      bot_id: requestId, // или нужно передать bot_id отдельно
      dry_run: dryRun || false
    };
    return safeApiCall(apiClient.post(`/requests/${requestId}/execute`, body));
  },
};

export default requestsApi;
