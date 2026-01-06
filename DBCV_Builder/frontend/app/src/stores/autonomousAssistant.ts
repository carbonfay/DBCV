import { defineStore } from 'pinia';
import { reactive } from 'vue';
import apiClient from '@/api/axios';
import { useAuthStore } from '@/stores';

interface ToolCall {
  tool: string;
  arguments: any;
  result: any;
  success: boolean;
  timestamp: string;
}

interface AutonomousSession {
  id: string;
  botId: string;
  status: 'idle' | 'generating' | 'completed' | 'error';
  prompt: string;
  context: any;
  result: any;
  error: string | null;
  toolCalls: ToolCall[];
  outputText: string;
  sessionId: string | null;
  createdAt: string;
  completedAt: string | null;
}

interface AutonomousSessions {
  [sessionId: string]: AutonomousSession;
}

interface GenerateRequest {
  prompt: string;
  bot_id?: string;
  context?: any;
}

interface GenerateResponse {
  success: boolean;
  response_id?: string;
  output_text: string;
  tool_calls?: ToolCall[];
  session_id?: string;
  error?: string;
}

export interface PlanStep {
  name: string;
  action: string;
  required_data: string[];
  notes?: string | null;
}

export interface PlanResponse {
  steps: PlanStep[];
  missing_data: string[];
  prompt_suggestion?: string | null;
}

interface AutonomousAssistantState {
  sessions: AutonomousSessions;
  plan: PlanResponse | null;
  planLoading: boolean;
  planError: string | null;
}

export const useAutonomousAssistantStore = defineStore('autonomousAssistant', {
  state: (): AutonomousAssistantState => ({
    sessions: reactive({}) as AutonomousSessions,
    plan: null,
    planLoading: false,
    planError: null,
  }),

  actions: {
    async generatePlan(prompt: string, botId?: string, context: any = {}): Promise<PlanResponse> {
      const authStore = useAuthStore();
      const token = authStore.accessToken;
      if (!token) {
        throw new Error('User not authenticated');
      }

      this.planLoading = true;
      this.planError = null;

      const request: GenerateRequest = { prompt };
      if (botId) {
        request.bot_id = botId;
      }
      if (context && Object.keys(context).length > 0) {
        request.context = context;
      }

      try {
        const response = await apiClient.post('/autonomous-assistant/plan', request, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        const data = response.data ?? {};
        const plan: PlanResponse = {
          steps: Array.isArray(data?.steps) ? data.steps : [],
          missing_data: Array.isArray(data?.missing_data) ? data.missing_data : [],
          prompt_suggestion: data?.prompt_suggestion ?? null,
        };

        this.plan = plan;
        this.planLoading = false;
        return plan;
      } catch (error: any) {
        const message =
          error?.response?.data?.detail ||
          error?.message ||
          'РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕСЃС‚СЂРѕРёС‚СЊ РїР»Р°РЅ';
        this.planLoading = false;
        this.planError = message;
        this.plan = null;
        throw new Error(message);
      }
    },

    clearPlan(): void {
      this.plan = null;
      this.planError = null;
      this.planLoading = false;
    },

    createSession(botId: string, prompt: string, context: any = {}): string {
      const sessionId = `autonomous-${Date.now()}-${Math.random().toString(36).substr(2, 8)}`;

      this.sessions[sessionId] = {
        id: sessionId,
        botId,
        status: 'idle',
        prompt,
        context,
        result: null,
        error: null,
        toolCalls: [],
        outputText: '',
        sessionId: null,
        createdAt: new Date().toISOString(),
        completedAt: null,
      };

      return sessionId;
    },

    async generateBot(sessionId: string, prompt: string, botId?: string, context: any = {}): Promise<void> {
      const session = this.sessions[sessionId];
      if (!session) {
        throw new Error(`Session ${sessionId} not found`);
      }

      const authStore = useAuthStore();
      const token = authStore.accessToken;
      if (!token) {
        throw new Error('User not authenticated');
      }

      try {
        session.status = 'generating';
        session.prompt = prompt;
        session.context = context;
        session.error = null;

        const request: GenerateRequest = { prompt, context };
        if (botId) {
          request.bot_id = botId;
        }

        const response = await apiClient.post('/autonomous-assistant/generate', request, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        const data: GenerateResponse = response.data;
        session.status = data.success ? 'completed' : 'error';
        session.outputText = data.output_text;
        session.toolCalls = data.tool_calls || [];
        session.sessionId = data.session_id || null;
        session.completedAt = new Date().toISOString();

        if (!data.success) {
          session.error = data.error || 'Generation failed';
          throw new Error(session.error);
        }
      } catch (error: any) {
        session.status = 'error';
        session.error = error?.message || 'Generation failed';
        session.completedAt = new Date().toISOString();
        throw error;
      }
    },

    async checkStatus(): Promise<any> {
      const authStore = useAuthStore();
      const token = authStore.accessToken;
      if (!token) {
        throw new Error('User not authenticated');
      }

        const response = await apiClient.get('/autonomous-assistant/status', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.data;
    },

    async testAssistant(): Promise<any> {
      const authStore = useAuthStore();
      const token = authStore.accessToken;
      if (!token) {
        throw new Error('User not authenticated');
      }

        const response = await apiClient.post('/autonomous-assistant/test', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.data;
    },

    getSession(sessionId: string): AutonomousSession | undefined {
      return this.sessions[sessionId];
    },

    getAllSessions(): AutonomousSession[] {
      return Object.values(this.sessions);
    },

    getSessionsForBot(botId: string): AutonomousSession[] {
      return Object.values(this.sessions).filter((session) => session.botId === botId);
    },

    removeSession(sessionId: string): void {
      delete this.sessions[sessionId];
    },

    clearAllSessions(): void {
      Object.keys(this.sessions).forEach((id) => delete this.sessions[id]);
    },

    getStats(): { total: number; completed: number; error: number; generating: number } {
      const sessions = Object.values(this.sessions);
      return {
        total: sessions.length,
        completed: sessions.filter((s) => s.status === 'completed').length,
        error: sessions.filter((s) => s.status === 'error').length,
        generating: sessions.filter((s) => s.status === 'generating').length,
      };
    },

    getToolHistory(sessionId: string): ToolCall[] {
      const session = this.sessions[sessionId];
      return session?.toolCalls || [];
    },

    getSessionResult(sessionId: string): any {
      const session = this.sessions[sessionId];
      return session?.result || null;
    },

    isSessionActive(sessionId: string): boolean {
      const session = this.sessions[sessionId];
      return session?.status === 'generating';
    },

    getLastSessionForBot(botId: string): AutonomousSession | null {
      const sessions = this.getSessionsForBot(botId);
      if (sessions.length === 0) {
        return null;
      }

      return sessions.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];
    },
  },
});

