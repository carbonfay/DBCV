import { defineStore } from 'pinia';
import credentialsApi from '@/api/services/credentialsApi';
import type { Credential } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useCredentialsStore = defineStore('credentials', {
  state: () => ({
    credentials: [] as Credential[],
    credentialId: null as string | null,
  }),

  actions: {
    async readCredentials(botId: string, params: Record<string, unknown> = {}) {
      const response = await credentialsApi.readCredentials(botId, params);
      if (response) {
        this.credentials = response.data;
      }
      return response;
    },

    async createCredential(botId: string, credentialData: Record<string, unknown>) {
      const response = await credentialsApi.createCredential(botId, credentialData);
      if (response && response.data) {
        this.credentials.push(response.data);
        return response.data;
      }
      return null;
    },

    async readCredential(botId: string, credId: string) {
      const response = await credentialsApi.readCredential(botId, credId);
      return response;
    },

    async updateCredential(botId: string, credId: string, credentialData: Record<string, unknown>) {
      const response = await credentialsApi.updateCredential(botId, credId, credentialData);
      if (response) {
        updateValueByIndex(this.credentials, credId, response.data);
      }
      return response;
    },

    async deleteCredential(botId: string, credId: string) {
      const response = await credentialsApi.deleteCredential(botId, credId);
      if (response) {
        this.credentials = this.credentials.filter((cred) => cred.id !== credId);
      }
      return response;
    },

    async makeDefaultCredential(botId: string, credId: string) {
      const response = await credentialsApi.makeDefaultCredential(botId, credId);
      if (response) {

        const targetCredential = this.credentials.find(cred => cred.id === credId);
        if (targetCredential) {
          this.credentials = this.credentials.map(cred => {
            if (cred.provider === targetCredential.provider && 
                cred.strategy === targetCredential.strategy) {
              return { ...cred, is_default: false };
            }
            return cred;
          });
          
          updateValueByIndex(this.credentials, credId, response.data);
        }
      }
      return response;
    },
  },
});
