<script setup lang="ts">
import MasterConnections from '@/components/tabs/botTabs/masterConnections.vue';
import MainSettings from '@/components/tabs/botTabs/mainSettings.vue';
import MainCredentials from '@/components/tabs/botTabs/mainCredentials.vue';
import MainLogs from '@/components/tabs/botTabs/mainLogs.vue';
import { ref, useTemplateRef } from 'vue';

const { botId, botInfo } = defineProps<{
  botId: string;
  botInfo?: Record<string, any>;
}>();

const tabs = [
  { name: 'main', label: 'Основное' },
  { name: 'masterConnections', label: 'Мастер-связи' },
  { name: 'credentials', label: 'Креды' },
  { name: 'logs', label: 'Журнал' },
];

const emit = defineEmits<{
  (e: 'action', payload: { action: string; data: any }): void;
}>();

const tabsComponent: Record<string, any> = {
  main: useTemplateRef('main'),
  masterConnections: useTemplateRef('masterConnections'),
  credentials: useTemplateRef('credentials'),
  logs: useTemplateRef('logs'),
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
  save: () => tryChangeTab(activeTab.value, 'main'),
});

const activeTab = ref(tabs[0].name);
</script>

<template>
  <BasePanelTabs :tabs="tabs" :active-tab="activeTab" @tab-change="tryChangeTab">
    <MainSettings
      ref="main"
      v-if="activeTab === 'main'"
      :botId="botId"
      :botInfo="botInfo"
      @update:botInfo="emit('action', { action: 'masterUpdate', data: $event })"
    />
    <MasterConnections
      ref="masterConnections"
      v-if="activeTab === 'masterConnections'"
      :botId="botId"
      :botInfo="botInfo"
    />
    <MainCredentials
      ref="credentials"
      v-if="activeTab === 'credentials'"
      :botId="botId"
    />
    <MainLogs ref="logs" v-if="activeTab === 'logs'" :botId="botId" />
  </BasePanelTabs>
</template>

<style scoped></style>
