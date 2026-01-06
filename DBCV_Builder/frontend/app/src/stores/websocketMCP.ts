import { defineStore } from 'pinia';
import { reactive } from 'vue';
import { useAuthStore } from '@/stores';

// TypeScript types
interface MCPStep {
  id: string;
  name: string;
  description: string;
  tool_used: string;
  reasoning: string;
  status: 'pending' | 'running' | 'completed';
  start_time?: string;
  end_time?: string;
  created_at?: string;
  input_data?: any;
  output_data?: any;
  progress?: number;
}

interface MCPSession {
  socket: WebSocket | null;
  botId: string;
  steps: MCPStep[];
  currentStep: MCPStep | null;
  connected: boolean;
  status: 'connecting' | 'connected' | 'generating' | 'completed' | 'error';
  result: any;
  error: string | null;
}

interface MCPSessions {
  [sessionId: string]: MCPSession;
}

export const useWebsocketMCPStore = defineStore('websocketMCP', {
  state: (): { sessions: MCPSessions } => ({
    sessions: reactive({}),
  }),
  actions: {
    async connect(sessionId: string, botId: string) {
      if (this.sessions[sessionId]?.socket) return;

      this.sessions[sessionId] = {
        socket: null,
        botId: botId,
        steps: reactive([]),
        currentStep: null,
        connected: false,
        status: 'connecting', // connecting, connected, generating, completed, error
        result: null,
        error: null,
      };

      try {
        // Получаем пользовательский токен авторизации
        const authStore = useAuthStore();
        const userToken = authStore.accessToken;
        
        if (!userToken) {
          throw new Error('User not authenticated');
        }
        
        // Генерируем session_id на фронтенде
        const backendSessionId = `mcp-session-${Date.now()}-${Math.random().toString(36).substr(2, 8)}`;
        
        // Подключаемся к MCP WebSocket API с пользовательским токеном
        const url = `ws://localhost:8005/ws/mcp?session_id=${backendSessionId}&bot_id=${botId}&token=${userToken}`;
        const socket = new WebSocket(url);
        this.sessions[sessionId].socket = socket;

      socket.onopen = () => {
        this.sessions[sessionId].connected = true;
        this.sessions[sessionId].status = 'connected';
        console.log(`MCP session ${sessionId} connected`);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          console.log('📨 MCP WebSocket message:', msg);

          switch (msg.type) {
            case 'status':
              this.handleStatus(sessionId, msg);
              break;
            case 'completion':
              this.handleCompletion(sessionId, msg);
              break;
            case 'error':
              this.handleError(sessionId, msg);
              break;
            // Обработка реальных инструментов MCP
            case 'ai_thinking':
              this.handleAIThinking(sessionId, msg);
              break;
            case 'ai_action':
              this.handleAIAction(sessionId, msg);
              break;
            case 'ai_result':
              this.handleAIResult(sessionId, msg);
              break;
            case 'ai_completion':
              this.handleAICompletion(sessionId, msg);
              break;
            case 'ai_warning':
              this.handleAIWarning(sessionId, msg);
              break;
            case 'ai_error':
              this.handleAIError(sessionId, msg);
              break;
            default:
              console.log('Unknown message type:', msg.type);
          }
        } catch (e) {
          console.error(`Ошибка парсинга сообщения MCP WebSocket для сессии ${sessionId}:`, e);
        }
      };

      socket.onerror = (e) => {
        console.error(`WebSocket ошибка у MCP сессии ${sessionId}:`, e);
        this.sessions[sessionId].status = 'error';
        this.sessions[sessionId].error = 'WebSocket connection error';
      };

      socket.onclose = () => {
        this.sessions[sessionId].connected = false;
        this.sessions[sessionId].socket = null;
        console.log(`WebSocket закрыт для MCP сессии ${sessionId}`);
      };

      } catch (error: any) {
        console.error(`Ошибка подключения к MCP WebSocket для сессии ${sessionId}:`, error);
        this.sessions[sessionId].status = 'error';
        this.sessions[sessionId].error = error.message;
      }
    },

    handleStatus(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`📊 Status update: ${msg.message}`);
      session.status = 'generating' as const;
    },

    handleCompletion(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`✅ Completion: ${JSON.stringify(msg.result)}`);
      session.status = 'completed' as const;
      session.result = msg.result;
    },

    handleStepProgress(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session || !session.currentStep) return;

      // Обновляем текущий шаг
      if (msg.progress) {
        session.currentStep.progress = msg.progress;
      }
      if (msg.reasoning) {
        session.currentStep.reasoning = msg.reasoning;
      }
    },

    handleStepCompleted(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session || !session.currentStep) return;

      session.currentStep.status = 'completed' as const;
      session.currentStep.output_data = msg.output_data;
      session.currentStep.end_time = new Date().toISOString();
      session.currentStep = null;
    },

    handleGenerationCompleted(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      session.status = 'completed' as const;
      session.result = msg.result;
    },

    handleModificationStarted(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      session.status = 'generating' as const;
      console.log(`🔧 Modification started for session ${sessionId}:`, msg);
    },

    handleModificationCompleted(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      session.status = 'completed' as const;
      session.result = msg.result;
      console.log(`✅ Modification completed for session ${sessionId}:`, msg);
    },

    handleModificationSuccess(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      // Не меняем статус, чтобы прогресс остался видимым
      // Просто показываем успешное завершение
      console.log(`🎉 Modification success for session ${sessionId}:`, msg);
      
      // Добавляем финальное сообщение в результат
      if (!session.result) {
        session.result = {};
      }
      session.result.success_message = msg.message;
      session.result.summary = msg.summary;
    },

    handleAIThinking(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`🤖 AI thinking: ${msg.message}`);
      console.log(`🧠 AI reasoning: ${msg.reasoning}`);
      
      // Добавляем AI мышление в шаги
      const thinkingStep = {
        id: `ai-thinking-${Date.now()}`,
        name: 'AI Анализ',
        description: msg.message,
        tool_used: 'ai_brain',
        reasoning: msg.reasoning || 'AI анализирует запрос с context7',
        status: 'running' as const,
        start_time: new Date().toISOString(),
        progress: 25,
        input_data: {
          reasoning: msg.reasoning,
          timestamp: msg.timestamp
        }
      };
      session.steps.push(thinkingStep);
      session.currentStep = thinkingStep;
    },

    handleAIAction(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`🔧 AI action: ${msg.message}`);
      console.log(`🛠️ Tool used: ${msg.tool_used}`);
      console.log(`💭 Reasoning: ${msg.reasoning}`);
      
      // Добавляем AI действие в шаги
      const actionStep = {
        id: `ai-action-${Date.now()}`,
        name: msg.tool_used || 'AI Действие',
        description: msg.message,
        tool_used: msg.tool_used || 'ai_tool',
        reasoning: msg.reasoning || 'AI выполняет действие с context7',
        status: 'running' as const,
        start_time: new Date().toISOString(),
        progress: 50,
        input_data: {
          tool_used: msg.tool_used,
          reasoning: msg.reasoning,
          step: msg.step,
          total_steps: msg.total_steps,
          timestamp: msg.timestamp
        }
      };
      session.steps.push(actionStep);
      session.currentStep = actionStep;
    },

    handleAIResult(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session || !session.currentStep) return;

      console.log(`✅ AI result: ${msg.message}`);
      console.log(`📊 Tool result:`, msg.tool_result);
      console.log(`🎯 Success: ${msg.success}`);
      
      // Обновляем текущий шаг с результатом
      session.currentStep.status = 'completed' as const;
      session.currentStep.progress = 100;
      session.currentStep.end_time = new Date().toISOString();
      session.currentStep.output_data = {
        tool_result: msg.tool_result,
        success: msg.success,
        message: msg.message,
        timestamp: msg.timestamp
      };
      session.currentStep = null;
    },

    handleAICompletion(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`🎉 AI completion: ${msg.message}`);
      console.log(`📈 Summary:`, msg.summary);
      
      session.status = 'completed' as const;
      session.result = {
        success: msg.summary?.overall_success || true,
        message: msg.message,
        summary: msg.summary,
        ai_reasoning: msg.summary?.ai_reasoning,
        tool_history: msg.summary?.tool_history || [],
        total_actions: msg.summary?.total_actions || 0,
        successful_actions: msg.summary?.successful_actions || 0,
        failed_actions: msg.summary?.failed_actions || 0
      };
    },

    handleAIWarning(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`⚠️ AI warning: ${msg.message}`);
      console.log(`🧠 AI reasoning: ${msg.reasoning}`);
      
      // Добавляем предупреждение в шаги
      const warningStep = {
        id: `ai-warning-${Date.now()}`,
        name: 'AI Предупреждение',
        description: msg.message,
        tool_used: 'ai_warning',
        reasoning: msg.reasoning || 'AI обнаружил проблему',
        status: 'completed' as const,
        start_time: new Date().toISOString(),
        end_time: new Date().toISOString(),
        progress: 100,
        input_data: {
          reasoning: msg.reasoning,
          timestamp: msg.timestamp
        },
        output_data: {
          warning: msg.message,
          reasoning: msg.reasoning
        }
      };
      session.steps.push(warningStep);
    },

    handleAIError(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      console.log(`❌ AI error: ${msg.message}`);
      console.log(`💥 Error details:`, msg.error);
      
      session.status = 'error' as const;
      session.error = msg.error || msg.message;
      
      // Добавляем ошибку в шаги
      const errorStep = {
        id: `ai-error-${Date.now()}`,
        name: 'AI Ошибка',
        description: msg.message,
        tool_used: 'ai_error',
        reasoning: 'AI столкнулся с ошибкой',
        status: 'completed' as const,
        start_time: new Date().toISOString(),
        end_time: new Date().toISOString(),
        progress: 100,
        input_data: {
          error: msg.error,
          timestamp: msg.timestamp
        },
        output_data: {
          error: msg.error,
          message: msg.message
        }
      };
      session.steps.push(errorStep);
    },

    handleError(sessionId: string, msg: any) {
      const session = this.sessions[sessionId];
      if (!session) return;

      session.status = 'error' as const;
      session.error = msg.error;
    },

    // Отправка промпта для генерации
    sendPrompt(sessionId: string, prompt: string, context: any = {}, mode: string = 'build') {
      const session = this.sessions[sessionId];
      if (!session || !session.socket) {
        console.error('WebSocket не подключен для сессии:', sessionId);
        return;
      }

      const message = {
        type: mode === 'build' ? 'generate' : 'modify',
        prompt: prompt,
        context: context,
      };

      session.socket.send(JSON.stringify(message));
      session.status = 'generating' as const;
    },

    // Отправка промпта для модификации бота
    sendModificationPrompt(sessionId: string, prompt: string, context: any = {}, mode: string = 'modify') {
      const session = this.sessions[sessionId];
      if (!session || !session.socket) {
        console.error('WebSocket не подключен для сессии:', sessionId);
        return;
      }

      const message = {
        type: 'modify',
        prompt: prompt,
        context: context,
        mode: mode,
      };

      session.socket.send(JSON.stringify(message));
      session.status = 'generating' as const;
    },

    disconnect(sessionId: string) {
      const session = this.sessions[sessionId];
      if (session?.socket) {
        session.socket.close();
        session.socket = null;
        session.connected = false;
      }
      this.removeSession(sessionId);
    },

    removeSession(sessionId: string) {
      delete this.sessions[sessionId];
    },

    getSession(sessionId: string) {
      return this.sessions[sessionId];
    },

    // Получить все шаги для сессии
    getSteps(sessionId: string) {
      const session = this.sessions[sessionId];
      return session?.steps || [];
    },
  },
});
