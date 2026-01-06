import apiClient, { safeApiCall } from '@/api/axios';

const messagesApi = {
  readMessages(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/messages/', { params }));
  },

  createMessage(messageData: Record<string, unknown>) {
    const formData = new FormData();
    for (const key in messageData) {
      if (messageData.hasOwnProperty(key)) {
        formData.append(key, messageData[key] as string | Blob);
      }
    }

    return safeApiCall(
      apiClient.post('/messages/', messageData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    );
  },

  sendMessage(text: string, channel_id: string) {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('channel_id', channel_id);

    return safeApiCall(
      apiClient.post('/messages/send_message', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    );
  },

  readMessage(messageId: string) {
    return safeApiCall(apiClient.get(`/messages/${messageId}`));
  },

  updateMessage(messageId: string, messageData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/messages/${messageId}`, messageData));
  },

  deleteMessage(messageId: string) {
    return safeApiCall(apiClient.delete(`/messages/${messageId}`));
  },
};

export default messagesApi;
