<template>
  <div>
    <div v-if="stepLogs.length" class="logs-container">
      <div class="logs-header">
        <span class="logs-count">Кол-во записей: {{ stepLogs.length }}</span>
      </div>
      <div class="logs-list">
        <div
          v-for="(log, index) in stepLogs"
          :key="index"
          class="log-entry"
          :class="`log-${log.level.toLowerCase()}`"
        >
          <div class="log-header">
            <span class="log-level" :class="`level-${log.level.toLowerCase()}`">
              {{ log.level }}
            </span>
            <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
          </div>
          <div class="log-message">{{ log.message }}</div>
        </div>
      </div>
    </div>
    <div v-else class="logs-empty">
      <p class="section-text">В данный момент журнал пуст</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
// @ts-ignore
import { useWebsocketBotStore } from '@/stores';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  botId: {
    type: String,
    required: false,
  },
});

const websocketStore = useWebsocketBotStore();

const stepLogs = computed(() => {
  const botId = props.botId || Object.keys(websocketStore.bots)[0];

  if (!botId) {
    return [];
  }

  const logs = websocketStore.getStepLogs(botId, props.node.id);
  return logs;
});

const formatTimestamp = (timestamp: string) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString('ru-RU');
};
</script>

<style scoped>
.section-text {
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  color: #fff;
}

.logs-container {
  max-height: 90%;
  overflow-y: auto;
}

.logs-header {
  margin-bottom: 15px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgb(75, 93, 104);
  font-size: 12px;
  color: rgb(162, 162, 162);
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.log-entry {
  background-color: #1f2937;
  padding: 0.5rem;
  border-radius: 0.375rem;
  white-space: pre-wrap;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-timestamp {
  font-size: 11px;
  color: rgb(162, 162, 162);
}

.log-message {
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.log-level {
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.level-info {
  background-color: #3b82f6;
}

.level-warning {
  background-color: #f59e0b;
}

.level-error {
  background-color: #ef4444;
}

.level-debug {
  background-color: #6b7280;
}
</style>
