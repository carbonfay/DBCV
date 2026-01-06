<template>
  <div
    :class="['bot-panel', expanded ? 'expanded' : 'collapsed']"
    :style="{
      width: expanded ? '450px' : '291px',
      height: expanded ? '100vh' : 'auto',
    }"
  >
    <div class="panel-header" @click="expanded = !expanded">
      <h2 class="panel-title">
        Переменные
        <span>({{ variableCount }})</span>
      </h2>
      <button class="toggle-button">
        <SmallScreenIcon v-if="expanded" />
        <FullScreenIcon v-else />
      </button>
    </div>

    <div v-if="expanded" class="panel-content">
      <table class="custom-table">
        <tbody>
          <RowViewer v-for="(val, key) in variables" :key="key" :k="key" :val="val" :depth="0" />
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
// @ts-ignore
import { FullScreenIcon, SmallScreenIcon } from '@/components/icons';
// @ts-ignore
import { useWebsocketBotStore } from '@/stores';
import RowViewer from '@/components/ui/RowViewer.vue';

const props = defineProps<{
  botId: string;
}>();

const websocketStore = useWebsocketBotStore();
const expanded = ref(false);

const botData = computed(() => websocketStore.getBot(props.botId) ?? {});
const variables = computed(() => botData.value.variables ?? {});
const variableCount = computed(() => Object.keys(variables.value).length);
</script>

<style scoped>
.bot-panel {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 10;
  border: 1px solid rgb(51, 64, 71);
  border-radius: 9px;
  box-shadow: 0px 2px 2px 0px rgba(0, 0, 0, 0.15);
  background: rgb(77, 77, 77);
  transition: all 0.3s ease;
  padding: 12px 15px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.panel-title {
  margin: 0;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.1;
  text-transform: uppercase;
}

.toggle-button {
  color: #3b82f6;
}

.panel-content {
  max-height: 100%;
  overflow: auto;
  border-top: 1px solid #fff;
  margin-top: 12px;
  padding-bottom: 30px;
}

.expanded {
  bottom: 0;
  right: 0;
  border-radius: 0;
}

.custom-table {
  table-layout: auto;
  width: 100%;
  font-size: 0.875rem;
  border-collapse: collapse;
}
</style>
