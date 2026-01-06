import apiClient, { safeApiCall } from '@/api/axios';

const channelsApi = {
  readChannels(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/channels/', { params }));
  },

  createChannel(channelData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/channels/', channelData));
  },

  readUserChannels(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/channels/', { params }));
  },

  readChannelById(channelId: string) {
    return safeApiCall(apiClient.get(`/channels/${channelId}`));
  },

  updateChannel(channelId: string, channelData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/channels/${channelId}`, channelData));
  },

  deleteChannel(channelId: string) {
    return safeApiCall(apiClient.delete(`/channels/${channelId}`));
  },

  readChannelMessages(channelId: string, skip?: number, limit?: number) {
    return safeApiCall(
      apiClient.get(`/channels/${channelId}/messages`, {
        params: { skip, limit },
      })
    );
  },

  subscribe(channelId: string, botIds: string[]) {
    return safeApiCall(apiClient.post(`/channels/${channelId}/subscribe`, botIds));
  },

  unsubscribe(channelId: string, botIds: string[]) {
    return safeApiCall(apiClient.post(`/channels/${channelId}/unsubscribe`, botIds));
  },
};

export default channelsApi;
