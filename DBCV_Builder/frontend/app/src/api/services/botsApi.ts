import apiClient, { safeApiCall } from '@/api/axios';

const botsApi = {
  readBots(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/bots/', { params }));
  },
  createBot(botData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/bots/', botData));
  },
  readBot(botId: string) {
    return safeApiCall(apiClient.get(`/bots/${botId}`));
  },
  updateBot(botId: string, botData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/bots/${botId}`, botData));
  },
  deleteBot(botId: string) {
    return safeApiCall(apiClient.delete(`/bots/${botId}`));
  },
  importBot(file: File, targetBotId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = targetBotId 
      ? `/bots/import?target_bot_id=${targetBotId}`
      : '/bots/import';
    
    return safeApiCall(apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }));
  },
  exportBot(botId: string) {
    return safeApiCall(apiClient.get(`/bots/export/${botId}`, {
      responseType: 'blob',
    }));
  },
};

export default botsApi;
