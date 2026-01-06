import { defineStore } from 'pinia';
import notesApi from '@/api/services/notesApi';
import type { Note } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useNotesStore = defineStore('notes', {
  state: () => ({
    notes: [] as Note[],
  }),

  actions: {
    async readNotes(params: Record<string, unknown> = {}) {
      const response = await notesApi.readNotes(params);
      if (response) {
        this.notes = response.data;
      }
      return response;
    },

    async createNote(noteData: Record<string, unknown>) {
      const response = await notesApi.createNote(noteData);
      if (response) {
        this.notes.push(response.data);
      }
      return response.data;
    },

    async updateNote(noteId: string, noteData: Record<string, unknown>) {
      const response = await notesApi.updateNote(noteId, noteData);
      if (response) {
        updateValueByIndex(this.notes, noteId, response.data);
      }
      return response;
    },

    async deleteNote(noteId: string) {
      const response = await notesApi.deleteNote(noteId);
      if (response) {
        this.notes = this.notes.filter((note) => note.id !== noteId);
      }
      return response;
    },
  },
});
