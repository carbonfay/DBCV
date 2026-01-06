import apiClient, { safeApiCall } from '@/api/axios';

const cronsApi = {
  readCrons(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/crons/', { params }));
  },

  createCron(cronData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/crons/', cronData));
  },

  updateCron(cronId: string, cronData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/crons/${cronId}`, cronData));
  },

  deleteCron(cronId: string) {
    return safeApiCall(apiClient.delete(`/crons/${cronId}`));
  },
};

export default cronsApi;
