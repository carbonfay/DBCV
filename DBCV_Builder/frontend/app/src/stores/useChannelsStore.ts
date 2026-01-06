import { defineStore } from 'pinia';
import channelApi from '@/api/services/channelsApi';
import { WEBSOCKET_BASE_URL } from '@/api/axios';
import type { Channel, Message } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useChannelsStore = defineStore('channels', {
  state: () => ({
    channels: [] as Channel[],
    userChannels: [] as Channel[],
    messages: [] as Message[],
    currentChannel: null as Channel | null,
  }),

  actions: {
    async readChannels() {
      const response = await channelApi.readChannels({ skip: 0 });
      if (response) {
        this.channels = response.data;
      }
      return response;
    },

    async readUserChannels() {
      const response = await channelApi.readUserChannels({ skip: 0 });
      if (response) {
        this.userChannels = response.data;
      }
      return response;
    },

    async readChannelById(channelId: string) {
      const response = await channelApi.readChannelById(channelId);
      if (response) {
        this.currentChannel = response.data;
      }
      return response;
    },

    async createChannel(channelData: Record<string, unknown>) {
      const response = await channelApi.createChannel(channelData);
      if (response) {
        this.channels.push(response.data);
      }
      return response.data;
    },

    async updateChannel(channelId: string, channelData: Record<string, unknown>) {
      const response = await channelApi.updateChannel(channelId, channelData);
      if (response) {
        updateValueByIndex(this.channels, channelId, response.data);
      }
      return response;
    },

    async deleteChannel(channelId: string) {
      const response = await channelApi.deleteChannel(channelId);
      if (response) {
        this.channels = this.channels.filter((channel) => channel.id !== channelId);
      }
      return response;
    },

    async fetchMessagesByChannel(channelId: string, skip?: number, limit?: number) {
      const response = await channelApi.readChannelMessages(channelId, skip, limit);
      if (response) {
        this.messages = response.data;
      }
      return response;
    },

    async subscribeToChannel(channelId: string, botIds: string[]) {
      const response = await channelApi.subscribe(channelId, botIds);
      return response;
    },

    async unsubscribeToChannel(channelId: string, botIds: string[]) {
      const response = await channelApi.unsubscribe(channelId, botIds);
      return response;
    },

    getWebSocketUrl(channelId: string, token: string) {
      return `${WEBSOCKET_BASE_URL}?channel_id=${channelId}&token=${token}`;
    },
  },
});
