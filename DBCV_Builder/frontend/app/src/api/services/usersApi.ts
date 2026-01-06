import apiClient, { safeApiCall } from '@/api/axios';

const usersApi = {
  readUsers(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/users/', { params }));
  },

  createUser(userData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/users/', userData));
  },

  readUserById(userId: string) {
    return safeApiCall(apiClient.get(`/users/${userId}`));
  },

  updateUser(userId: string, userData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/users/${userId}`, userData));
  },

  deleteUser(userId: string) {
    return safeApiCall(apiClient.delete(`/users/${userId}`));
  },

  readCurrentUser() {
    return safeApiCall(apiClient.get(`/users/me`));
  },
};

export default usersApi;
