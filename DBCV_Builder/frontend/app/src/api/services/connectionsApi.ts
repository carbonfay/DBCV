import apiClient, { safeApiCall } from '@/api/axios';

const connectionsApi = {
  readConnections(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/connections/', { params }));
  },

  createConnection(connectionData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/connections/', connectionData));
  },

  updateConnection(connectionId: string, connectionData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/connections/${connectionId}`, connectionData));
  },

  deleteConnection(connectionId: string) {
    return safeApiCall(apiClient.delete(`/connections/${connectionId}`));
  },
};

export default connectionsApi;
