import { defineStore } from 'pinia';
import trackingApi, {
  type GenerationSession,
  type GenerationStep,
  type SessionSummary,
  type TrackingEvent,
  type WebSocketMessage,
} from '@/api/services/trackingApi';

export const useTrackingStore = defineStore('tracking', {
  state: () => ({
    currentSession: null as GenerationSession | null,
    steps: [] as GenerationStep[],
    events: [] as TrackingEvent[],
    isConnected: false,
    progress: {
      total_steps: 0,
      completed_steps: 0,
      percentage: 0
    }
  }),

  getters: {
    sessionStatus: (state) => state.currentSession?.status || 'pending',
    isSessionActive: (state) => state.currentSession?.status === 'in_progress',
    completedSteps: (state) => state.steps.filter(step => step.status === 'completed'),
    failedSteps: (state) => state.steps.filter(step => step.status === 'failed'),
    inProgressSteps: (state) => state.steps.filter(step => step.status === 'in_progress'),
  },

  actions: {
    // Начать новую сессию отслеживания
    async startSession(data: { user_prompt: string; bot_name: string; user_id?: string }) {
      const response = await trackingApi.startSession(data);
      if (response?.data) {
        this.currentSession = response.data;
        this.steps = [];
        this.events = [];
        this.updateProgress();
      }
      return response;
    },

    // Загрузить данные сессии
    async loadSessionSummary(sessionId: string) {
      const response = await trackingApi.getSessionSummary(sessionId);
      if (response?.data) {
        const summary: SessionSummary = response.data;
        this.currentSession = summary.session;
        this.steps = summary.steps;
        this.progress = summary.progress;
      }
      return response;
    },

    async loadSessionEvents(sessionId: string) {
      const response = await trackingApi.getSessionEvents(sessionId);
      if (response?.data?.events) {
        this.events = (response.data.events as TrackingEvent[]).slice();
      }
      return response;
    },

    // Обновить статус сессии
    async updateSessionStatus(sessionId: string) {
      const response = await trackingApi.getSessionStatus(sessionId);
      if (response?.data) {
        this.currentSession = response.data;
      }
      return response;
    },

    // Загрузить шаги сессии
    async loadSessionSteps(sessionId: string) {
      const response = await trackingApi.getSessionSteps(sessionId);
      if (response?.data) {
        this.steps = response.data;
        this.updateProgress();
      }
      return response;
    },

    // Применить изменения
    async applyChanges(sessionId: string) {
      const response = await trackingApi.applyChanges(sessionId);
      if (response?.data) {
        // Обновляем статус сессии после применения изменений
        await this.updateSessionStatus(sessionId);
      }
      return response;
    },

    // Откатить изменения
    async rollbackChanges(sessionId: string) {
      const response = await trackingApi.rollbackChanges(sessionId);
      if (response?.data) {
        // Обновляем статус сессии после отката изменений
        await this.updateSessionStatus(sessionId);
      }
      return response;
    },

    // Обновить прогресс
    updateProgress() {
      this.progress.total_steps = this.steps.length;
      this.progress.completed_steps = this.completedSteps.length;
      this.progress.percentage = this.progress.total_steps > 0 
        ? (this.progress.completed_steps / this.progress.total_steps) * 100 
        : 0;
    },

    // Обработка WebSocket сообщений
    handleWebSocketMessage(message: any) {
      const typedMessage = message as WebSocketMessage;
      switch (message.type) {
        case 'session_started':
          this.currentSession = message.data;
          break;
        case 'step_added':
          this.steps.push(message.data);
          this.updateProgress();
          break;
        case 'step_started':
          this.updateStepStatus(message.step_id, 'in_progress');
          break;
        case 'step_completed':
          this.updateStepStatus(message.step_id, 'completed', message.data);
          this.updateProgress();
          break;
        case 'session_finalized':
          if (this.currentSession) {
            this.currentSession.status = 'completed';
            this.currentSession.final_bot_id = message.data.final_bot_id;
            this.currentSession.total_duration = message.data.total_duration;
          }
          break;
        case 'tracking_event': {
          const incoming = typedMessage.event;
          if (incoming && !this.events.some(evt => evt.id === incoming.id)) {
            this.events.push(incoming);
            if (this.events.length > 200) {
              this.events.shift();
            }
          }
          break;
        }
      }
    },

    // Обновить статус шага
    updateStepStatus(stepId: string, status: GenerationStep['status'], data?: any) {
      const step = this.steps.find(s => s.id === stepId);
      if (step) {
        step.status = status;
        if (data) {
          Object.assign(step, data);
        }
      }
    },

    // Сбросить состояние
    reset() {
      this.currentSession = null;
      this.steps = [];
      this.events = [];
      this.isConnected = false;
      this.progress = {
        total_steps: 0,
        completed_steps: 0,
        percentage: 0
      };
    }
  }
});
