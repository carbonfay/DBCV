<template>
  <div v-if="logs.length" ref="logsContainer" class="logs-container">
    <div class="logs-list">
      <div v-for="(log, index) in logs" :key="index" class="log-entry">
        {{ log }}
      </div>
    </div>
  </div>
  <div v-else class="logs-empty">В данный момент журнал пуст</div>
</template>

<script setup lang="ts">
import { computed, onMounted, nextTick, ref, watch } from 'vue';
// @ts-ignore
import { useWebsocketBotStore } from '@/stores';

const props = defineProps<{
  botId: string;
}>();

const websocketStore = useWebsocketBotStore();
const logsContainer = ref<HTMLElement | null>(null);
const logs = computed(() => websocketStore.getBot(props.botId)?.logs ?? []);

const scrollToBottom = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
  }
};

watch(
  logs,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
  { deep: true }
);

onMounted(() => {
  nextTick(() => {
    scrollToBottom();
  });
});
</script>

<style scoped>
.logs-container {
  font-size: 12px;
  max-height: 90%;
  overflow-y: auto;
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

.logs-empty {
  font-size: 12px;
  font-weight: 700;
}
</style>
