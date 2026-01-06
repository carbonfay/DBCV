import { defineStore } from 'pinia';
import botsApi from '@/api/services/botsApi';
import type { Bot } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useBotsStore = defineStore('bots', {
  state: () => ({
    bots: [] as Bot[],
    botId: null as string | null,
  }),

  actions: {
    async readBots(params: Record<string, unknown> = {}) {
      const response = await botsApi.readBots(params);
      if (response) {
        this.bots = response.data;
      }
      return response;
    },

    async createBot(botData: Record<string, unknown>) {
      const response = await botsApi.createBot(botData);
      if (response) {
        this.bots.push(response.data);
      }
      return response.data;
    },

    async readBot(botId: string) {
      const response = await botsApi.readBot(botId);
      return response;
    },

    async updateBot(botId: string, botData: Record<string, unknown>) {
      const response = await botsApi.updateBot(botId, botData);
      if (response) {
        updateValueByIndex(this.bots, botId, response.data);
      }
      return response;
    },

    async deleteBot(botId: string) {
      const response = await botsApi.deleteBot(botId);
      if (response) {
        this.bots = this.bots.filter((bot) => bot.id !== botId);
      }
      return response;
    },

    async importBot(file: File, targetBotId?: string) {
      const response = await botsApi.importBot(file, targetBotId);
      if (response) {
        if (targetBotId) {
          // Замена структуры существующего бота
          updateValueByIndex(this.bots, targetBotId, response.data);
        } else {
          // Создание нового бота
          this.bots.push(response.data);
        }
      }
      return response;
    },

    async exportBot(botId: string) {
      const response = await botsApi.exportBot(botId);
      if (response) {
        // Создаем blob и скачиваем файл
        const blob = new Blob([response.data], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `bot-${botId}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
      return response;
    },
  },
});
