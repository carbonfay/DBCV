import apiClient, { safeApiCall } from '@/api/axios';

const connectionGroupsApi = {
  readConnectionGroups(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/connection_groups/', { params }));
  },

  createConnectionGroup(connectionGroupData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/connection_groups/', connectionGroupData));
  },

  updateConnectionGroup(connectionGroupId: string, connectionGroupData: Record<string, unknown>) {
    return safeApiCall(
      apiClient.patch(`/connection_groups/${connectionGroupId}`, connectionGroupData)
    );
  },

  deleteConnectionGroup(connectionGroupId: string) {
    return safeApiCall(apiClient.delete(`/connection_groups/${connectionGroupId}`));
  },
};

export default connectionGroupsApi;
