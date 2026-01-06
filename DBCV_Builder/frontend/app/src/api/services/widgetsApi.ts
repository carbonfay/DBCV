import apiClient, { safeApiCall } from '@/api/axios';

const widgetsApi = {
  readWidgets(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/widgets/', { params }));
  },

  createWidget(widgetData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/widgets/', widgetData));
  },

  updateWidget(widgetId: string, widgetData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/widgets/${widgetId}`, widgetData));
  },

  deleteWidget(widgetId: string) {
    return safeApiCall(apiClient.delete(`/widgets/${widgetId}`));
  },
};

export default widgetsApi;
