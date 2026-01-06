import apiClient, { safeApiCall } from '@/api/axios';

const notesApi = {
  readNotes(params: Record<string, unknown> = {}) {
    return safeApiCall(apiClient.get('/notes/', { params }));
  },

  createNote(noteData: Record<string, unknown>) {
    return safeApiCall(apiClient.post('/notes/', noteData));
  },

  updateNote(noteId: string, noteData: Record<string, unknown>) {
    return safeApiCall(apiClient.patch(`/notes/${noteId}`, noteData));
  },

  deleteNote(noteId: string) {
    return safeApiCall(apiClient.delete(`/notes/${noteId}`));
  },
};

export default notesApi;
