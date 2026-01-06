import apiClient, { safeApiCall } from '@/api/axios';

export interface GenerationSession {
  id: string;
  user_prompt: string;
  bot_name: string;
  created_at: number;
  updated_at: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  final_bot_id?: string;
  total_duration?: number;
}

export interface GenerationStep {
  id: string;
  type: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  start_time?: number;
  end_time?: number;
  duration?: number;
  tool_used?: string;
  reasoning?: string;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
}

export interface SessionSummary {
  session: GenerationSession;
  steps: GenerationStep[];
  progress: {
    total_steps: number;
    completed_steps: number;
    percentage: number;
  };
}

export interface TrackingEvent {
  id: string;
  type: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface WebSocketMessage {
  type:
    | 'session_started'
    | 'step_added'
    | 'step_started'
    | 'step_completed'
    | 'session_finalized'
    | 'tracking_event';
  session_id: string;
  step_id?: string;
  data?: any;
  event?: TrackingEvent;
}

const trackingApi = {
  // Начать новую сессию отслеживания
  startSession(data: { user_prompt: string; bot_name: string; user_id?: string }) {
    return safeApiCall(apiClient.post('/api/v1/tracking/sessions/start', data));
  },

  // Получить статус сессии
  getSessionStatus(sessionId: string) {
    return safeApiCall(apiClient.get(`/api/v1/tracking/sessions/${sessionId}/status`));
  },

  // Получить шаги сессии
  getSessionSteps(sessionId: string) {
    return safeApiCall(apiClient.get(`/api/v1/tracking/sessions/${sessionId}/steps`));
  },

  // Получить полную сводку сессии
  getSessionSummary(sessionId: string) {
    return safeApiCall(apiClient.get(`/api/v1/tracking/sessions/${sessionId}/summary`));
  },

  getSessionEvents(sessionId: string) {
    return safeApiCall(apiClient.get(`/api/v1/tracking/sessions/${sessionId}/events`));
  },

  // Применить изменения
  applyChanges(sessionId: string) {
    return safeApiCall(apiClient.post(`/api/v1/tracking/sessions/${sessionId}/apply`));
  },

  // Откатить изменения
  rollbackChanges(sessionId: string) {
    return safeApiCall(apiClient.post(`/api/v1/tracking/sessions/${sessionId}/rollback`));
  },
};

export default trackingApi;
