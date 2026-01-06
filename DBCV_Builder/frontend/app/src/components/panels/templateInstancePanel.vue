<script setup lang="ts">
import { ref, useTemplateRef } from 'vue';
import TemplateInfoTab from '@/components/tabs/templateInstanceTabs/templateInfo.vue';
import VariablesTab from '@/components/tabs/templateInstanceTabs/variables.vue';
import StepsTab from '@/components/tabs/templateInstanceTabs/steps.vue';
import ConnectionsTab from '@/components/tabs/templateInstanceTabs/connections.vue';

const { node } = defineProps<{
  node: unknown;
}>();

const tabs = [
  { name: 'templateInfo', label: 'Основное' },
  { name: 'variables', label: 'Переменные' },
  { name: 'steps', label: 'Шаги' },
  { name: 'connections', label: 'Связи' },
];

const activeTab = ref(tabs[0].name);

const tabsComponent: Record<string, any> = {
  templateInfo: useTemplateRef('templateInfo'),
  variables: useTemplateRef('variables'),
  steps: useTemplateRef('steps'),
  connections: useTemplateRef('connections'),
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
  save: () => tryChangeTab(activeTab.value, 'templateInfo'),
});

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
  <BasePanelTabs :active-tab="activeTab" :tabs="tabs" @tab-change="tryChangeTab">
    <TemplateInfoTab
      v-if="activeTab === 'templateInfo'"
      ref="templateInfo"
      :node="node"
      @update-node="updateNode"
    />
    <VariablesTab
      v-if="activeTab === 'variables'"
      ref="variables"
      :node="node"
      @update-node="updateNode"
    />
    <StepsTab v-if="activeTab === 'steps'" ref="steps" :node="node" />
    <ConnectionsTab
      v-if="activeTab === 'connections'"
      ref="connections"
      :node="node"
      @graphUpdate-node="graphUpdateNode"
    />
  </BasePanelTabs>
</template>

<style scoped></style>
