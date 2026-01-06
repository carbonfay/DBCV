import apiClient, { safeApiCall } from '@/api/axios';

const stepsApi = {
  readSteps(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/steps/', { params }));
  },

  createStep(stepData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/steps/', stepData));
  },

  updateStep(stepId: string, stepData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/steps/${stepId}`, stepData));
  },

  deleteStep(stepId: string) {
    return safeApiCall(apiClient.delete(`/steps/${stepId}`));
  },

  runStep(stepId: string, data: { 
    variables?: Record<string, any>, 
    bot_id?: string, 
    context?: Record<string, any> 
  }) {
    return safeApiCall(apiClient.post(`/steps/${stepId}/run`, data));
  },
};

export default stepsApi;
