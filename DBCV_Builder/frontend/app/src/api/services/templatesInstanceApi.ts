import apiClient, { safeApiCall } from '@/api/axios';

const templatesInstanceApi = {
  readTemplatesInstances(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/template_instance/', { params }));
  },

  createTemplateInstance(instanceData: Record<string, unknown>, botId: string) {
    return safeApiCall(apiClient.post(`/template_instance/?bot_id=${botId}`, instanceData));
  },

  readTemplateInstance(instanceId: string) {
    return safeApiCall(apiClient.get(`/template_instance/${instanceId}`));
  },

  updateTemplateInstance(instanceId: string, instanceData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/template_instance/${instanceId}`, instanceData));
  },

  deleteTemplateInstance(instanceId: string) {
    return safeApiCall(apiClient.delete(`/template_instance/${instanceId}`));
  },
};

export default templatesInstanceApi;
