import { defineStore } from 'pinia';
import templatesInstanceApi from '@/api/services/templatesInstanceApi';
import type { TemplateInstance } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useTemplatesInstanceStore = defineStore('templatesInstance', {
  state: () => ({
    templatesInstances: [] as TemplateInstance[],
  }),

  actions: {
    async readTemplatesInstances(params: Record<string, unknown> = {}) {
      const response = await templatesInstanceApi.readTemplatesInstances(params);
      if (response) {
        this.templatesInstances = response.data;
      }
      return response;
    },

    async createTemplateInstance(instanceData: Record<string, unknown>) {
      const { bot_id, ...rest } = instanceData as { bot_id: string; [key: string]: unknown };
      const response = await templatesInstanceApi.createTemplateInstance(rest, bot_id);
      if (response) {
        this.templatesInstances.push(response.data);
      }
      return response;
    },

    async readTemplateInstance(instanceId: string) {
      const response = await templatesInstanceApi.readTemplateInstance(instanceId);
      return response;
    },

    async updateTemplateInstance(instanceId: string, instanceData: Record<string, unknown>) {
      const response = await templatesInstanceApi.updateTemplateInstance(instanceId, instanceData);
      if (response) {
        updateValueByIndex(this.templatesInstances, instanceId, response.data);
      }
      return response;
    },

    async deleteTemplateInstance(instanceId: string) {
      const response = await templatesInstanceApi.deleteTemplateInstance(instanceId);
      if (response) {
        this.templatesInstances = this.templatesInstances.filter(
          (instance) => instance.id !== instanceId
        );
      }
      return response;
    },
  },
});
