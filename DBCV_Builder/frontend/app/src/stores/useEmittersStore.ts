import { defineStore } from 'pinia';
import emittersApi from '@/api/services/emittersApi';
import type { Emitter } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useEmittersStore = defineStore('emitters', {
  state: () => ({
    emitters: [] as Emitter[],
  }),

  actions: {
    async readEmitters(params: Record<string, unknown> = {}) {
      const response = await emittersApi.readEmitters(params);
      if (response) {
        this.emitters = response.data;
      }
      return response;
    },

    async createEmitter(emitterData: Record<string, unknown>) {
      const response = await emittersApi.createEmitter(emitterData);
      if (response) {
        this.emitters.push(response.data);
      }
      return response.data;
    },

    async readEmitter(emitterId: string) {
      const response = await emittersApi.readEmitter(emitterId);
      return response;
    },

    async updateEmitter(emitterId: string, emitterData: Record<string, unknown>) {
      const response = await emittersApi.updateEmitter(emitterId, emitterData);
      if (response) {
        updateValueByIndex(this.emitters, emitterId, response.data);
      }
      return response;
    },

    async deleteEmitter(emitterId: string) {
      const response = await emittersApi.deleteEmitter(emitterId);
      if (response) {
        this.emitters = this.emitters.filter((emitter) => emitter.id !== emitterId);
      }
      return response;
    },
  },
});
