import { defineStore } from 'pinia';
import cronsApi from '@/api/services/cronsApi';
import type { Cron } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useCronsStore = defineStore('crons', {
  state: () => ({
    crons: [] as Cron[],
  }),

  actions: {
    async readCrons(params: Record<string, unknown> = {}) {
      const response = await cronsApi.readCrons(params);
      if (response) {
        this.crons = response.data;
      }
      return response.data;
    },

    async createCron(cronData: Record<string, unknown>) {
      const response = await cronsApi.createCron(cronData);
      if (response) {
        this.crons.push(response.data);
      }
      return response;
    },

    async updateCron(cronId: string, cronData: Record<string, unknown>) {
      const response = await cronsApi.updateCron(cronId, cronData);
      if (response) {
        updateValueByIndex(this.crons, cronId, response.data);
      }
      return response;
    },

    async deleteCron(cronId: string) {
      const response = await cronsApi.deleteCron(cronId);
      if (response) {
        this.crons = this.crons.filter((cron) => cron.id !== cronId);
      }
      return response;
    },
  },
});
