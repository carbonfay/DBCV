import { defineStore } from 'pinia';
import templatesApi from '@/api/services/templatesApi';
import type { Template } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useTemplatesStore = defineStore('templates', {
  state: () => ({
    templates: [] as Template[],
  }),

  actions: {
    async readTemplates(params: Record<string, unknown> = {}) {
      const response = await templatesApi.readTemplates(params);
      if (response) {
        this.templates = response.data;
      }
      return response;
    },

    async createTemplate(templateData: Record<string, unknown>) {
      const response = await templatesApi.createTemplate(templateData);
      if (response) {
        this.templates.push(response.data);
      }
      return response;
    },

    async readTemplate(templateId: string) {
      const response = await templatesApi.readTemplate(templateId);
      return response;
    },

    async updateTemplate(templateId: string, templateData: Record<string, unknown>) {
      const response = await templatesApi.updateTemplate(templateId, templateData);
      if (response) {
        updateValueByIndex(this.templates, templateId, response.data);
      }
      return response;
    },

    async deleteTemplate(templateId: string) {
      const response = await templatesApi.deleteTemplate(templateId);
      if (response) {
        this.templates = this.templates.filter((template) => template.id !== templateId);
      }
      return response;
    },
  },
});
