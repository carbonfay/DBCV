<script lang="ts" setup>
import Tab1 from '@/components/tabs/nodeTabs/tab1.vue';
import Tab2 from '@/components/tabs/nodeTabs/tab2.vue';
import Tab3 from '@/components/tabs/nodeTabs/tab3.vue';
import Tab4 from '@/components/tabs/nodeTabs/tab4.vue';
import { ref, useTemplateRef } from 'vue';

const { node, initActiveTab, botId } = defineProps<{
  node: any;
  initActiveTab?: string;
  botId?: string;
}>();

const tabs = [
  { name: 'main', label: 'Основное' },
  { name: 'representation', label: 'Ответ' },
  { name: 'connections', label: 'Связи' },
  { name: 'log', label: 'Журнал' },
];

const activeTab = ref(localStorage.getItem('simple:lastTab') || initActiveTab || 'main');

const setActiveTabAndPersist = (nextTab: string) => {
  activeTab.value = nextTab;
  localStorage.setItem('simple:lastTab', nextTab);
};

const tabsComponent: Record<string, any> = {
  main: useTemplateRef('main'),
  representation: useTemplateRef('representation'),
  connections: useTemplateRef('connections'),
  log: useTemplateRef('log'),
};

const tryChangeTab = async (tab: string, nextTab: string) => {
  let caughtError = null;
  let tabComponent;
  if (tab in tabsComponent) tabComponent = tabsComponent[tab].value;
  else tabComponent = null;
  if (tabComponent?.isSomethingChanged && window.confirm('Хотите сохранить изменения?')) {
    if (tabComponent?.trySave)
      try {
        await tabComponent?.trySave();
        setActiveTabAndPersist(nextTab);
      } catch (error) {
        caughtError = error;
        console.error('Error saving tab:', error);
      }
    else {
      await tabComponent?.save();
    }
  }
  if (caughtError) return;
  else setActiveTabAndPersist(nextTab);
};

const emit = defineEmits<{
  (e: 'action', payload: { action: string; data: any }): void;
}>();

const updateNode = (updatedNode: unknown) => {
  emit('action', { action: 'update', data: updatedNode });
};

const graphUpdateNode = (updatedNode: unknown) => {
  emit('action', { action: 'graphUpdate', data: updatedNode });
};

defineExpose({
  save: () => tryChangeTab(activeTab.value, activeTab.value),
});
</script>

<template>
  <BasePanelTabs :active-tab="activeTab" :tabs="tabs" @tab-change="tryChangeTab">
    <Tab1 v-if="activeTab === 'main'" ref="main" :node="node" @update-node="updateNode" />
    <Tab2
      v-if="activeTab === 'representation'"
      ref="representation"
      :node="node"
      @graphUpdate-node="graphUpdateNode"
    />
    <Tab3
      v-if="activeTab === 'connections'"
      ref="connections"
      :node="node"
      @graphUpdate-node="graphUpdateNode"
    />
    <Tab4 v-if="activeTab === 'log'" ref="log" :node="node as any" :bot-id="botId" />
  </BasePanelTabs>
</template>

<style scoped></style>
