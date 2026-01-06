import { defineStore } from 'pinia';
import authApi from '@/api/services/authApi';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null as string | null,
  }),

  actions: {
    async login(username: string, password: string) {
      const response = await authApi.login({
        grant_type: 'password',
        username,
        password,
        scope: '',
        client_id: 'string',
        client_secret: 'string',
      });

      if (response) {
        this.accessToken = response.data.access_token;
      }

      return response;
    },

    logout() {
      this.accessToken = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('users');
    },
  },
  persist: {
    key: 'accessToken',
    storage: localStorage,
    serializer: {
      serialize: (state) => state.accessToken || '',
      deserialize: (value) => ({ accessToken: value || null }),
    },
  },
});
