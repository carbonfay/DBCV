import { defineStore } from 'pinia';
import messagesApi from '@/api/services/messagesApi';
import type { Message } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useMessagesStore = defineStore('messages', {
  state: () => ({
    messages: [] as Message[],
  }),

  actions: {
    async readMessages(params: Record<string, unknown> = {}) {
      const response = await messagesApi.readMessages(params);
      if (response) {
        this.messages = response.data;
      }
      return response;
    },

    async createMessage(messageData: Record<string, unknown>) {
      const response = await messagesApi.createMessage(messageData);
      if (response) {
        this.messages.push(response.data);
      }
      return response;
    },

    async readMessage(messageId: string) {
      const response = await messagesApi.readMessage(messageId);
      return response;
    },

    async updateMessage(messageId: string, messageData: Record<string, unknown>) {
      const response = await messagesApi.updateMessage(messageId, messageData);
      if (response) {
        updateValueByIndex(this.messages, messageId, response.data);
      }
      return response;
    },

    async deleteMessage(messageId: string) {
      const response = await messagesApi.deleteMessage(messageId);
      if (response) {
        this.messages = this.messages.filter((message) => message.id !== messageId);
      }
      return response;
    },

    async sendMessage(text: string, channelId: string) {
      const response = await messagesApi.sendMessage(text, channelId);
      return response;
    },
  },
});
