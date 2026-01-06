<script setup lang="ts">
import settingsTab from '@/components/tabs/emittersTabs/main.vue';
import logTab from '@/components/tabs/emittersTabs/log.vue';
import messageTab from '@/components/tabs/nodeTabs/tab2.vue';
import { ref, useTemplateRef } from 'vue';

const { node } = defineProps<{
  node: unknown;
}>();

const tabs = [
  { name: 'settings', label: 'Настройки' },
  { name: 'message', label: 'Сообщение' },
  { name: 'log', label: 'Журнал' },
];

const tabsComponent: Record<string, any> = {
  settings: useTemplateRef('settings'),
  message: useTemplateRef('message'),
  log: useTemplateRef('log'),
};

const tryChangeTab = async (tab: string, nextTab: string) => {
  let caughtError = null;
  const tabComponent = tabsComponent[tab].value;
  if (tabComponent?.isSomethingChanged && window.confirm('Хотите сохранить изменения?')) {
    if (tabComponent?.trySave)
      try {
        await tabComponent?.trySave();
        activeTab.value = nextTab;
      } catch (error) {
        caughtError = error;
        console.error('Error saving tab:', error);
      }
    else {
      await tabComponent.save();
    }
  }
  if (caughtError) return;
  else activeTab.value = nextTab;
};

defineExpose({
  save: () => tryChangeTab(activeTab.value, 'settings'),
});

const activeTab = ref(tabs[0].name);

const emit = defineEmits<{
  (e: 'action', payload: { action: string; data: any }): void;
}>();

const updateNode = (updatedNode: unknown) => {
  emit('action', { action: 'update', data: updatedNode });
};

const graphUpdateNode = (updatedNode: unknown) => {
  emit('action', { action: 'graphUpdate', data: updatedNode });
};
</script>

<template>
  <BasePanelTabs :tabs="tabs" :active-tab="activeTab" @tab-change="tryChangeTab">
    <settingsTab
      ref="settings"
      v-if="activeTab === 'settings'"
      :node="node"
      @update-node="updateNode"
    />
    <messageTab
      ref="message"
      v-if="activeTab === 'message'"
      :node="node"
      @graphUpdate-node="graphUpdateNode"
    />
    <logTab ref="log" v-if="activeTab === 'log'" />
  </BasePanelTabs>
</template>

<style scoped></style>
