import { defineStore } from 'pinia';
import { reactive } from 'vue';

export const useWebsocketBotStore = defineStore('websocket', {
  state: () => ({
    bots: reactive({}),
  }),
  actions: {
    connect(botId, token, initialVariables = {}) {
      if (this.bots[botId]?.socket) return;

      this.bots[botId] = {
        socket: null,
        variables: reactive({ ...initialVariables }),
        logs: reactive([]),
        stepLogs: reactive({}),
        connected: false,
      };

      const url = `ws://localhost:8003/ws/bot?bot_id=${botId}&token=${token}`;
      const socket = new WebSocket(url);
      this.bots[botId].socket = socket;

      socket.onopen = () => {
        this.bots[botId].connected = true;
        console.log(`Bot ${botId} connected`);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === 'variables') {
            const vars = this.bots[botId].variables;
            for (const key in vars) delete vars[key];
            Object.assign(vars, msg.message);
          } else if (msg.type === 'logs') {
            this.bots[botId].logs.push(msg.message);

            if (msg.step_id) {
              const stepId = msg.step_id;
              if (!this.bots[botId].stepLogs[stepId]) {
                this.bots[botId].stepLogs[stepId] = reactive([]);
              }
              this.bots[botId].stepLogs[stepId].push({
                level: msg.level || 'INFO',
                message: msg.message,
                timestamp: new Date().toISOString(),
              });
            }
          }
        } catch (e) {
          console.error(`Ошибка парсинга сообщения WS для агента ${botId}:`, e);
        }
      };

      socket.onerror = (e) => {
        console.error(`WebSocket ошибка у бота ${botId}:`, e);
      };

      socket.onclose = () => {
        this.bots[botId].connected = false;
        this.bots[botId].socket = null;
        console.log(`WebSocket закрыт для бота ${botId}`);
      };
    },

    disconnect(botId) {
      const bot = this.bots[botId];
      if (bot?.socket) {
        bot.socket.close();
        bot.socket = null;
        bot.connected = false;
      }
      this.removeBot(botId);
    },

    removeBot(botId) {
      delete this.bots[botId];
    },

    getBot(botId) {
      return this.bots[botId];
    },

    // Получить логи для конкретного шага
    getStepLogs(botId, stepId) {
      const bot = this.bots[botId];
      if (bot?.stepLogs && bot.stepLogs[stepId]) {
        return bot.stepLogs[stepId];
      }
      return [];
    },
  },
});
