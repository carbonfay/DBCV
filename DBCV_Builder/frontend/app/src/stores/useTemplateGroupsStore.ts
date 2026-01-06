import { defineStore } from 'pinia';
import templateGroupApi from '@/api/services/templateGroupApi';
import type { TemplateGroups } from '@/types/store_types';

export const useTemplateGroupsStore = defineStore('templateGroups', {
  state: () => ({
    templatesGroups: [] as TemplateGroups[],
  }),

  actions: {
    async readTemplateGroups(params: Record<string, unknown> = {}) {
      const response = await templateGroupApi.readTemplateGroups(params);
      if (response) {
        this.templatesGroups = response.data;
      }
      return response;
    },

    async readTemplateGroup(groupId: string) {
      const response = await templateGroupApi.readTemplateGroup(groupId);
      return response;
    },

    async createTemplateGroup(groupData: Record<string, unknown>) {
      const response = await templateGroupApi.createTemplateGroup(groupData);
      if (response) {
        await this.readTemplateGroups();
      }
      return response;
    },

    async updateTemplateGroup(groupId: string, groupData: Record<string, unknown>) {
      const response = await templateGroupApi.updateTemplateGroup(groupId, groupData);
      if (response) {
        await this.readTemplateGroups();
      }
      return response;
    },

    async deleteTemplateGroup(groupId: string) {
      const response = await templateGroupApi.deleteTemplateGroup(groupId);
      if (response) {
        await this.readTemplateGroups();
      }
      return response;
    },

    async addTemplateToGroup(groupId: string, templateId: string) {
      const response = await templateGroupApi.addTemplateToGroup(groupId, templateId);
      if (response) {
        await this.readTemplateGroups();
      }
      return response;
    },

    async removeTemplateFromGroup(groupId: string, templateId: string) {
      const response = await templateGroupApi.removeTemplateToGroup(groupId, templateId);
      if (response) {
        await this.readTemplateGroups();
      }
      return response;
    },
  },
});
