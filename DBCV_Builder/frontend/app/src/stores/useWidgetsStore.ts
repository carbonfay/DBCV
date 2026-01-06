import { defineStore } from 'pinia';
import widgetApi from '@/api/services/widgetsApi';
import type { Widget } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useWidgetsStore = defineStore('widgets', {
  state: () => ({
    widgets: [] as Widget[],
  }),

  actions: {
    async readWidgets(params: Record<string, unknown> = {}) {
      const response = await widgetApi.readWidgets(params);
      if (response) {
        this.widgets = response.data;
      }
      return response;
    },

    async createWidget(widgetData: Record<string, unknown>) {
      const response = await widgetApi.createWidget(widgetData);
      if (response) {
        this.widgets.push(response.data);
      }
      return response.data;
    },

    async updateWidget(widgetId: string, widgetData: Record<string, unknown>) {
      const response = await widgetApi.updateWidget(widgetId, widgetData);
      if (response) {
        updateValueByIndex(this.widgets, widgetId, response.data);
      }
      return response;
    },

    async deleteWidget(widgetId: string) {
      const response = await widgetApi.deleteWidget(widgetId);
      if (response) {
        this.widgets = this.widgets.filter((widget) => widget.id !== widgetId);
      }
      return response;
    },
  },
});
