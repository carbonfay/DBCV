import { defineStore } from 'pinia';
import stepsApi from '@/api/services/stepsApi';
import type { Step } from '@/types/store_types';
import { updateValueByIndex } from '@/helpers';

export const useStepsStore = defineStore('steps', {
  state: () => ({
    steps: [] as Step[],
  }),

  actions: {
    async readSteps(params: Record<string, unknown> = {}) {
      const response = await stepsApi.readSteps(params);
      if (response) {
        this.steps = response.data;
      }
      return response;
    },

    async createStep(stepData: Record<string, unknown>) {
      const response = await stepsApi.createStep(stepData);
      if (response) {
        this.steps.push(response.data);
      }
      return response.data;
    },

    async updateStep(stepId: string, stepData: Record<string, unknown>) {
      const response = await stepsApi.updateStep(stepId, stepData);
      if (response) {
        updateValueByIndex(this.steps, stepId, response.data);
      }
      return response;
    },

    async deleteStep(stepId: string) {
      const response = await stepsApi.deleteStep(stepId);
      if (response) {
        this.steps = this.steps.filter((step) => step.id !== stepId);
      }
      return response;
    },

    async runStep(stepId: string, data: Record<string, unknown>) {
      const response = await stepsApi.runStep(stepId, data);
      return response;
    },
  },
});
