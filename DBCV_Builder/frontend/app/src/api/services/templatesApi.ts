import apiClient, { safeApiCall } from '@/api/axios';

const templatesApi = {
  readTemplates(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/templates/', { params }));
  },

  createTemplate(templateData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/templates/', templateData));
  },

  readTemplate(templateId: string) {
    return safeApiCall(apiClient.get(`/templates/${templateId}`));
  },

  updateTemplate(templateId: string, templateData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/templates/${templateId}`, templateData));
  },

  deleteTemplate(templateId: string) {
    return safeApiCall(apiClient.delete(`/templates/${templateId}`));
  },
};

export default templatesApi;
