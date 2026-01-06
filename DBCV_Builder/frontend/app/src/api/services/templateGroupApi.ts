import apiClient, { safeApiCall } from '@/api/axios';

const templateGroupApi = {
  readTemplateGroups(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/template_group/', { params }));
  },
  readTemplateGroup(groupId: string) {
    return safeApiCall(apiClient.get(`/api/v1/template_group/${groupId}`));
  },
  createTemplateGroup(groupData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/template_group/', groupData));
  },
  updateTemplateGroup(groupId: string, groupData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/template_group/${groupId}`, groupData));
  },
  deleteTemplateGroup(groupId: string) {
    return safeApiCall(apiClient.delete(`/template_group/${groupId}`));
  },
  addTemplateToGroup(groupId: string, templateId: string) {
    return safeApiCall(apiClient.post(`/template_group/${groupId}/add_template/${templateId}`));
  },
  removeTemplateToGroup(groupId: string, templateId: string) {
    return safeApiCall(apiClient.post(`/template_group/${groupId}/remove_template/${templateId}`));
  },
};

export default templateGroupApi;
