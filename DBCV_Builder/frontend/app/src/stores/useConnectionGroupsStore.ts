import { defineStore } from 'pinia';
import connectionGroupsApi from '@/api/services/connectionGroupsApi';
import type { ConnectionGroup } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useConnectionGroupsStore = defineStore('connectionGroups', {
  state: () => ({
    connectionGroups: [] as ConnectionGroup[],
  }),

  actions: {
    async readConnectionGroups(params: Record<string, unknown> = {}) {
      const response = await connectionGroupsApi.readConnectionGroups(params);
      if (response) {
        this.connectionGroups = response.data;
      }
      return response;
    },

    async createConnectionGroup(connectionGroupData: Record<string, unknown>) {
      const response = await connectionGroupsApi.createConnectionGroup(connectionGroupData);
      if (response) {
        this.connectionGroups.push(response.data);
      }
      return response.data;
    },

    async updateConnectionGroup(
      connectionGroupId: string,
      connectionGroupData: Record<string, unknown>
    ) {
      const response = await connectionGroupsApi.updateConnectionGroup(
        connectionGroupId,
        connectionGroupData
      );
      if (response) {
        updateValueByIndex(this.connectionGroups, connectionGroupId, response.data);
      }
      return response;
    },

    async deleteConnectionGroup(connectionGroupId: string) {
      const response = await connectionGroupsApi.deleteConnectionGroup(connectionGroupId);
      if (response) {
        this.connectionGroups = this.connectionGroups.filter(
          (connectionGroup) => connectionGroup.id !== connectionGroupId
        );
      }
      return response;
    },
  },
});
