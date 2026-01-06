import apiClient, { safeApiCall } from '@/api/axios';

const emittersApi = {
  readEmitters(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/emitters/', { params }));
  },

  createEmitter(emitterData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/emitters/', emitterData));
  },

  readEmitter(emitterId: string) {
    return safeApiCall(apiClient.get(`/emitters/${emitterId}`));
  },

  updateEmitter(emitterId: string, emitterData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/emitters/${emitterId}`, emitterData));
  },

  deleteEmitter(emitterId: string) {
    return safeApiCall(apiClient.delete(`/emitters/${emitterId}`));
  },
};

export default emittersApi;
