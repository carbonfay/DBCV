<template>
  <div class="generation-tracker">
    <!-- Информация о сессии -->
    <div class="session-info">
      <h3>Генерация бота: {{ currentSession?.bot_name || 'Загрузка...' }}</h3>
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${progress.percentage}%` }"
        ></div>
      </div>
      <div class="session-stats">
        <span>Шагов: {{ progress.total_steps }}</span>
        <span>Выполнено: {{ progress.completed_steps }}</span>
        <span>Время: {{ formatDuration(totalDuration) }}</span>
        <span class="connection-status" :class="{ connected: isConnected }">
          {{ isConnected ? 'Подключено' : 'Отключено' }}
        </span>
      </div>
    </div>

    <div class="event-stream" v-if="events.length">
      <h4>��� ������ ����������</h4>
      <div
        v-for="event in events"
        :key="event.id"
        class="event-item"
        :class="`event-${event.type}`"
      >
        <div class="event-meta">
          <span class="event-time">{{ formatEventTime(event.timestamp) }}</span>
          <span class="event-type">{{ getEventLabel(event.type) }}</span>
        </div>
        <div class="event-body">{{ formatEventDescription(event) }}</div>
      </div>
    </div>

    <!-- ??????????? ?????????? -->
    <div class="steps-container">
      <div 
        v-for="step in steps" 
        :key="step.id"
        class="step"
        :class="getStepClass(step)"
        :data-step-id="step.id"
      >
        <div class="step-header">
          <span class="step-type">{{ getStepTypeLabel(step.type) }}</span>
          <span class="step-name">{{ step.name }}</span>
          <span class="step-status">{{ getStepStatusIcon(step.status) }}</span>
        </div>
        <div class="step-details">
          <p class="step-description">{{ step.description }}</p>
          <p v-if="step.reasoning" class="step-reasoning">{{ step.reasoning }}</p>
          <div class="step-timing">
            <span v-if="step.duration">
              Время выполнения: {{ step.duration.toFixed(1) }}с
            </span>
            <span v-else-if="step.status === 'in_progress'">
              Выполняется...
            </span>
          </div>
          <div v-if="step.tool_used" class="step-tools">
            <span class="tool-used">{{ step.tool_used }}</span>
          </div>
          <div v-if="step.error_message" class="step-error">
            <strong>Ошибка:</strong> {{ step.error_message }}
          </div>
        </div>
      </div>
    </div>

    <!-- Действия -->
    <div v-if="currentSession?.status === 'completed'" class="actions">
      <BaseButton
        size="medium"
        styleType="success"
        @click="applyChanges"
        :disabled="isApplying"
      >
        {{ isApplying ? 'Применяется...' : 'Применить изменения' }}
      </BaseButton>
      <BaseButton
        size="medium"
        styleType="warning"
        @click="rollbackChanges"
        :disabled="isRollingBack"
      >
        {{ isRollingBack ? 'Откатывается...' : 'Откатить изменения' }}
      </BaseButton>
    </div>

    <!-- Кнопка закрытия -->
    <div class="tracker-actions">
      <BaseButton
        size="medium"
        styleType="secondary"
        @click="closeTracker"
      >
        Закрыть
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useTrackingStore } from '@/stores';
import { storeToRefs } from 'pinia';
import notyf from '@/plugins/notyf';
import type { GenerationStep, TrackingEvent } from '@/api/services/trackingApi';

interface GenerationTrackerProps {
  sessionId: string;
}

const props = defineProps<GenerationTrackerProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const trackingStore = useTrackingStore();
const { currentSession, steps, progress, isConnected, events } = storeToRefs(trackingStore);

const isApplying = ref(false);
const isRollingBack = ref(false);
const ws = ref<WebSocket | null>(null);

// Вычисляемые свойства
const totalDuration = computed(() => {
  if (!currentSession.value?.total_duration) {
    return steps.value.reduce((total: number, step: GenerationStep) => total + (step.duration || 0), 0);
  }
  return currentSession.value.total_duration;
});

const formatEventTime = (timestamp: number) => {
  if (!timestamp) return '';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
};

const eventLabels: Record<string, string> = {
  ai_thought: 'AI размышляет',
  ai_tool_update: 'Обновление шага',
  ai_error: 'Ошибка',
  ai_completed: 'Завершено',
};

const getEventLabel = (eventType: string) => eventLabels[eventType] || eventType;

const formatEventDescription = (event: TrackingEvent) => {
  const data = (event.data || {}) as Record<string, unknown>;
  switch (event.type) {
    case 'ai_thought':
      return typeof data['chunk'] === 'string' ? (data['chunk'] as string) : JSON.stringify(data);
    case 'ai_tool_update': {
      const delta = (data['delta'] as Record<string, unknown>) || {};
      if (typeof delta['step_name'] === 'string') {
        return `Инструмент: ${String(delta['step_name'])}`;
      }
      return JSON.stringify(delta || data);
    }
    case 'ai_error':
      return typeof data['message'] === 'string' ? (data['message'] as string) : JSON.stringify(data);
    case 'ai_completed':
      return typeof data['output_text'] === 'string'
        ? (data['output_text'] as string)
        : 'Ассистент завершил работу';
    default:
      return JSON.stringify(data);
  }
};

// Методы
const getStepClass = (step: GenerationStep) => {
  const classes = [];
  if (step.status === 'in_progress') classes.push('in-progress');
  if (step.status === 'completed') classes.push('completed');
  if (step.status === 'failed') classes.push('error');
  return classes;
};

const getStepTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'planning': 'ПЛАНИРОВАНИЕ',
    'step_creation': 'СОЗДАНИЕ ШАГА',
    'bot_creation': 'СОЗДАНИЕ БОТА',
    'validation': 'ПРОВЕРКА',
    'finalization': 'ЗАВЕРШЕНИЕ'
  };
  return labels[type] || type.toUpperCase();
};

const getStepStatusIcon = (status: GenerationStep['status']) => {
  const icons: Record<GenerationStep['status'], string> = {
    'pending': '⏳',
    'in_progress': '🔄',
    'completed': '✅',
    'failed': '❌',
    'skipped': '⏭️'
  };
  return icons[status] || '❓';
};

const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}с`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}м ${remainingSeconds.toFixed(1)}с`;
};

// WebSocket соединение
const connectWebSocket = () => {
  if (!props.sessionId) return;

  const wsUrl = `ws://localhost:8003/api/v1/tracking/sessions/${props.sessionId}/ws`;
  ws.value = new WebSocket(wsUrl);

  ws.value.onopen = () => {
    trackingStore.isConnected = true;
    console.log('WebSocket connected');
  };

  ws.value.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      trackingStore.handleWebSocketMessage(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.value.onclose = () => {
    trackingStore.isConnected = false;
    console.log('WebSocket disconnected');
    // Попытка переподключения через 3 секунды
    setTimeout(() => {
      if (props.sessionId) {
        connectWebSocket();
      }
    }, 3000);
  };

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error);
    trackingStore.isConnected = false;
  };
};

const disconnectWebSocket = () => {
  if (ws.value) {
    ws.value.close();
    ws.value = null;
  }
};

// Действия
const applyChanges = async () => {
  if (!props.sessionId) return;

  isApplying.value = true;
  try {
    const response = await trackingStore.applyChanges(props.sessionId);
    if (response?.data) {
      notyf.success('Изменения применены успешно!');
    } else {
      notyf.error('Не удалось применить изменения');
    }
  } catch (error) {
    notyf.error('Ошибка при применении изменений');
    console.error('Apply changes error:', error);
  } finally {
    isApplying.value = false;
  }
};

const rollbackChanges = async () => {
  if (!props.sessionId) return;

  isRollingBack.value = true;
  try {
    const response = await trackingStore.rollbackChanges(props.sessionId);
    if (response?.data) {
      notyf.success('Изменения откачены успешно!');
    } else {
      notyf.error('Не удалось откатить изменения');
    }
  } catch (error) {
    notyf.error('Ошибка при откате изменений');
    console.error('Rollback changes error:', error);
  } finally {
    isRollingBack.value = false;
  }
};

const closeTracker = () => {
  disconnectWebSocket();
  emit('close');
};

// Жизненный цикл
onMounted(async () => {
  // Загружаем начальные данные
  await trackingStore.loadSessionSummary(props.sessionId);
  await trackingStore.loadSessionEvents(props.sessionId);
  // Подключаемся к WebSocket
  connectWebSocket();
});

onUnmounted(() => {
  disconnectWebSocket();
});
</script>

<style scoped>
.generation-tracker {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: #313131;
  border-radius: 10px;
  color: #fff;
}

.session-info {
  background: #2a2a2a;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #444;
}

.session-info h3 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #444;
  border-radius: 10px;
  overflow: hidden;
  margin: 15px 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  transition: width 0.3s ease;
}

.session-stats {
  display: flex;
  gap: 20px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.session-stats span {
  color: #ccc;
  font-size: 14px;
}

.connection-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.connection-status.connected {
  background: #4caf50;
  color: #fff;
}

.connection-status:not(.connected) {
  background: #f44336;
  color: #fff;
}

.event-stream {
  margin-bottom: 20px;
  padding: 16px;
  background: #262626;
  border: 1px solid #444;
  border-radius: 8px;
}

.event-stream h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.event-item {
  background: #1f1f1f;
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
  border-left: 3px solid #4caf50;
}

.event-item.event-ai_tool_update {
  border-left-color: #00bcd4;
}

.event-item.event-ai_error {
  border-left-color: #f44336;
}

.event-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 6px;
}

.event-type {
  font-weight: 600;
  color: #fff;
}

.event-body {
  color: #ddd;
  line-height: 1.4;
  white-space: pre-wrap;
}


.steps-container {
  margin-bottom: 20px;
}

.step {
  border: 1px solid #444;
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
  background: #2a2a2a;
}

.step-header {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #3a3a3a;
  border-bottom: 1px solid #444;
}

.step-type {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  margin-right: 10px;
}

.step-name {
  flex: 1;
  font-weight: 600;
  color: #fff;
}

.step-status {
  font-size: 18px;
}

.step-details {
  padding: 15px;
}

.step-description {
  margin: 0 0 10px 0;
  color: #ccc;
  line-height: 1.4;
}

.step-reasoning {
  margin: 0 0 10px 0;
  font-style: italic;
  color: #aaa;
  line-height: 1.4;
}

.step-timing, .step-tools {
  font-size: 14px;
  color: #999;
  margin: 5px 0;
}

.tool-used {
  background: #555;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}

.step-error {
  margin-top: 10px;
  padding: 10px;
  background: #f44336;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
}

.step.in-progress {
  border-color: #ffc107;
  background: #3a3a2a;
}

.step.completed {
  border-color: #4caf50;
  background: #2a3a2a;
}

.step.error {
  border-color: #f44336;
  background: #3a2a2a;
}

.actions {
  margin: 20px 0;
  text-align: center;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.tracker-actions {
  margin-top: 20px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #444;
}
</style>
