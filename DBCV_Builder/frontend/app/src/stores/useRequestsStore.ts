import { defineStore } from 'pinia';
import requestsApi from '@/api/services/requestsApi';
import type { Request } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useRequestsStore = defineStore('requests', {
  state: () => ({
    requests: [] as Request[],
  }),

  actions: {
    async readRequests(params: Record<string, unknown> = {}) {
      const response = await requestsApi.readRequests(params);
      if (response) {
        this.requests = response.data;
      }
      return response;
    },

    async createRequest(requestData: Record<string, unknown>) {
      const response = await requestsApi.createRequest(requestData);
      if (response) {
        this.requests.push(response.data);
      }
      return response.data;
    },

    async updateRequest(requestId: string, requestData: Record<string, unknown>) {
      const response = await requestsApi.updateRequest(requestId, requestData);
      if (response) {
        updateValueByIndex(this.requests, requestId, response.data);
      }
      return response;
    },

    async deleteRequest(requestId: string) {
      const response = await requestsApi.deleteRequest(requestId);
      if (response) {
        this.requests = this.requests.filter((request) => request.id !== requestId);
      }
      return response;
    },

    async executeRequest(requestId: string, variables?: Record<string, unknown>, dryRun?: boolean) {
      const response = await requestsApi.executeRequest(requestId, variables, dryRun);
      return response;
    },
  },
});
