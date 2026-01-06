import apiClient, { safeApiCall } from '@/api/axios';

const presetsApi = {
  getCatalog(params: { category?: string } = {}) {
    return safeApiCall(apiClient.get('/presets/catalog', { params }));
  },

  createStepFromPreset(presetData: {
    preset_id: string;
    bot_id: string;
    config: Record<string, unknown>;
    name?: string;
    pos_x?: number;
    pos_y?: number;
  }) {
    return safeApiCall(apiClient.post('/presets/create-step', presetData));
  },
};

export default presetsApi;

