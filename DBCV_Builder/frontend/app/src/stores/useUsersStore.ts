import { defineStore } from 'pinia';
import usersApi from '@/api/services/usersApi';
import type { User } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [] as User[],
    currentUser: null as User | null,
  }),

  actions: {
    async readUsers() {
      const response = await usersApi.readUsers({ skip: 0 });
      if (response) {
        this.users = response.data;
      }
      return response;
    },

    async readCurrentUser() {
      const response = await usersApi.readCurrentUser();
      if (response) {
        this.currentUser = response.data;
      }
      return response;
    },

    async createUser(userData: Record<string, unknown>) {
      const response = await usersApi.createUser(userData);
      if (response) {
        this.users.push(response.data);
      }
      return response;
    },

    async readUserById(userId: string) {
      const response = await usersApi.readUserById(userId);
      return response;
    },

    async updateUser(userId: string, userData: Record<string, unknown>) {
      const response = await usersApi.updateUser(userId, userData);
      if (response) {
        updateValueByIndex(this.users, userId, response.data);
      }
      return response;
    },

    async deleteUser(userId: string) {
      const response = await usersApi.deleteUser(userId);
      if (response) {
        this.users = this.users.filter((user) => user.id !== userId);
      }
      return response;
    },
  },
  persist: {
    storage: localStorage,
  },
});
