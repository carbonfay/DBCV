<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.name"
      :class="{ active: activeTab === tab.name }"
      @click="handleTabClick(tab.name)"
    >
      {{ tab.label }}
    </button>
  </div>
  <slot />
</template>

<script lang="ts">
export default {
  name: 'BasePanelTabs',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import type { Tab } from '@/types/component_types';

interface Props {
  tabs: Tab[];
  activeTab: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'tab-change', currentTab: string, nextTab: string): void;
}>();

const handleTabClick = (nextTab: string) => {
  emit('tab-change', props.activeTab, nextTab);
};
</script>

<style scoped>
.tabs {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 7px;
  padding: 13px 0;
  overflow: auto;
}

.tabs button {
  padding: 10px;
  border-radius: 3px;
  color: rgb(162, 162, 162);
  font-size: 11px;
  font-weight: 700;
  line-height: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background-color 0.3s;
  text-transform: uppercase;
}

.tabs button.active {
  background: rgba(255, 255, 255, 1);
  color: rgb(40, 40, 40);
}

.tabs button:hover {
  background: rgba(255, 255, 255, 0.8);
  color: rgb(40, 40, 40);
}
</style>
