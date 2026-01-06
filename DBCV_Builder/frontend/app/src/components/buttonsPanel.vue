<template>
  <div class="buttons-panel">
    <button @click="createNode('simple')">
      <div class="text-btn">
        <PlusIcon class="icon" />
        <span>Блок</span>
      </div>
    </button>
    <div class="templates-dropdown">
      <button
        @click="toggleTemplatesDropdown"
        :class="['dropdown-toggle', { active: showTemplatesDropdown }]"
      >
        <i class="fas fa-chevron-up chevron-icon" :class="{ rotated: showTemplatesDropdown }"></i>
      </button>
      <div v-if="showTemplatesDropdown" class="dropdown-content">
        <button
          v-for="group in filteredTemplateGroups"
          :key="group.id"
          @click="selectGroup(group)"
          class="group-item"
        >
          {{ group.name }}
        </button>
        <button @click="selectOtherGroup" class="group-item">Другие</button>
      </div>
    </div>
    <button @click="createNode('emitter')">
      <ClockIcon class="icon" />
    </button>
    <button @click="createNode('note')">
      <MessageIcon class="icon" />
    </button>
    <button @click="openIntegrationsPalette">
      <i class="fa-solid fa-plug icon"></i>
    </button>
    <button @click="openPresetsPalette">
      <i class="fa-solid fa-puzzle-piece icon"></i>
    </button>
  </div>
  
  <!-- Модальные окна для панелей -->
  <div v-if="showIntegrationsPalette" class="palette-modal-overlay" @click="closeIntegrationsPalette">
    <div class="palette-modal" @click.stop>
      <IntegrationPalette
        @select="handleIntegrationSelect"
        @close="closeIntegrationsPalette"
      />
    </div>
  </div>
  
  <div v-if="showPresetsPalette" class="palette-modal-overlay" @click="closePresetsPalette">
    <div class="palette-modal" @click.stop>
      <PresetPalette
        @select="handlePresetSelect"
        @close="closePresetsPalette"
      />
    </div>
  </div>
  
  <!-- Модальное окно для настройки интеграции -->
  <IntegrationConfigModal
    v-if="selectedIntegration"
    :integration="selectedIntegration"
    :bot-id="botId"
    @close="closeIntegrationModal"
    @created="handleIntegrationCreated"
  />
  
  <!-- Модальное окно для настройки preset -->
  <PresetConfigModal
    v-if="selectedPreset"
    :preset="selectedPreset"
    :bot-id="botId"
    @close="closePresetModal"
    @created="handlePresetCreated"
  />
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue';
import { v4 as uuidv4 } from 'uuid';
import { PlusIcon, ClockIcon, MessageIcon } from '@/components/icons';
import IntegrationPalette from '@/components/panels/IntegrationPalette.vue';
import PresetPalette from '@/components/panels/PresetPalette.vue';
import IntegrationConfigModal from '@/components/modals/IntegrationConfigModal.vue';
import PresetConfigModal from '@/components/modals/PresetConfigModal.vue';
import integrationsApi from '@/api/services/integrationsApi';

const emit = defineEmits<{
  (e: 'add-node', payload: { type: string; name: string }): void;
  (e: 'select-template-group', group: any): void;
}>();

const props = defineProps<{
  templateGroupsInfo: any[];
  botId: string;
}>();

const showIntegrationsPalette = ref(false);
const showPresetsPalette = ref(false);
const selectedIntegration = ref(null);
const selectedPreset = ref(null);

const refreshBotData = inject<(() => Promise<void>) | null>('refreshBotData', null);

const openIntegrationsPalette = () => {
  showIntegrationsPalette.value = true;
};

const closeIntegrationsPalette = () => {
  showIntegrationsPalette.value = false;
};

const openPresetsPalette = () => {
  showPresetsPalette.value = true;
};

const closePresetsPalette = () => {
  showPresetsPalette.value = false;
};

const handleIntegrationSelect = async (integration: any): Promise<void> => {
  // Получаем полные метаданные интеграции
  try {
    const response = await integrationsApi.getMetadata(integration.id);
    if (response?.data) {
      selectedIntegration.value = response.data;
      closeIntegrationsPalette();
    } else {
      selectedIntegration.value = integration;
      closeIntegrationsPalette();
    }
  } catch (error) {
    console.error('Error loading integration metadata:', error);
    selectedIntegration.value = integration;
    closeIntegrationsPalette();
  }
};

const closeIntegrationModal = () => {
  selectedIntegration.value = null;
};

const handleIntegrationCreated = async (data: any): Promise<void> => {
  // Обновляем данные бота после создания шага
  if (refreshBotData) {
    await refreshBotData();
  }
  closeIntegrationModal();
};

const handlePresetSelect = async (preset: any): Promise<void> => {
  // Используем preset напрямую (он уже содержит все метаданные из catalog)
  selectedPreset.value = preset;
  closePresetsPalette();
};

const closePresetModal = () => {
  selectedPreset.value = null;
};

const handlePresetCreated = async (data: any): Promise<void> => {
  // Обновляем данные бота после создания шага
  if (refreshBotData) {
    await refreshBotData();
  }
  closePresetModal();
};

const showTemplatesDropdown = ref(false);

const filteredTemplateGroups = computed(() => {
  return props.templateGroupsInfo.filter((group: any) => group.templates && group.templates.length > 0);
});

const toggleTemplatesDropdown = () => {
  showTemplatesDropdown.value = !showTemplatesDropdown.value;
};

const selectGroup = (group: any) => {
  emit('select-template-group', group);
  showTemplatesDropdown.value = false;
};

const selectOtherGroup = () => {
  emit('select-template-group', {
    id: 'other',
    name: 'Другие',
    templates: [],
  });
  showTemplatesDropdown.value = false;
};

const createNode = (type: string) => {
  const stepName = getStepName(type);
  emit('add-node', { type, name: stepName });
};

const getStepName = (type: string) => {
  const uniqueId = uuidv4();
  const timestamp = Date.now().toString().slice(-4);
  switch (type) {
    case 'simple':
      return `Новый шаг ${uniqueId}`;
    case 'emitter':
      return `Эмиттер ${timestamp}`;
    case 'note':
      return `Заметка ${uniqueId}`;
    default:
      return 'Новый блок';
  }
};
</script>

<style scoped>
.buttons-panel {
  position: absolute;
  bottom: 30px;
  display: flex;
  justify-content: center;
  box-sizing: border-box;
  border: 1px solid rgb(48, 68, 81);
  border-radius: 10px;
  box-shadow: 0px 2px 4.9px 0px rgba(0, 0, 0, 0.25);
  background: linear-gradient(0deg, rgb(45, 45, 45), rgb(53, 53, 53) 100%);
  width: fit-content;
  padding: 15px;
  gap: 8px;
  left: 50%;
  transform: translate(-50%);
  z-index: 10;
}

.buttons-panel > *:nth-child(n + 3) {
  margin-left: 9px;
}

button {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.95;
  border: none;
  background: none;
  cursor: pointer;
}

button:hover {
  opacity: 1;
}

.text-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(21, 61, 81);
  border-radius: 6px;
  background: rgb(29, 76, 99);
  padding: 5px 8px;
  gap: 8px;
}

.icon {
  width: 20px;
  height: 20px;
}

.templates-dropdown {
  position: relative;
}

.dropdown-toggle {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.dropdown-toggle:hover {
  background: rgb(45, 45, 45);
}

.dropdown-toggle.active {
  background: rgb(45, 45, 45);
}

.dropdown-content {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 0;
  margin-bottom: 10px;
  background: rgb(45, 45, 45);
  border: 1px solid rgb(48, 68, 81);
  border-radius: 6px;
  min-width: 150px;
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.group-item {
  width: 100%;
  padding: 10px 15px;
  text-align: left;
  color: white;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 1px solid rgb(48, 68, 81);
}

.group-item:last-child {
  border-bottom: none;
}

.group-item:hover {
  background: rgba(29, 76, 99, 0.3);
}

.chevron-icon {
  font-size: 12px;
  transition: transform 0.3s ease;
  color: white;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
  opacity: 0.5;
}

.palette-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.palette-modal {
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  border-radius: 8px;
  overflow: hidden;
}
</style>
