<template>
  <div class="aside">
    <BaseResizeBar ref="resize-bar" :init-value="300" :max="500" :min="200" position="right" />
    <div class="btns-block">
      <button @click="goBack">
        <i class="fa-solid fa-arrow-left"></i>
        Назад
      </button>
      <button @click="openMcpPrompt">
        <i class="fa-solid fa-robot"></i>
        MCP
      </button>
      <button @click="openSettings">
        <SettingsIcon class="settings-icon" />
      </button>
    </div>
    
    <!-- Кнопки импорта и экспорта -->
    <div class="import-export-block">
      <button @click="exportBot" class="export-btn" title="Экспорт бота">
        <DownloadIcon class="icon" />
        Экспорт
      </button>
      <button @click="openImportModal" class="import-btn" title="Импорт структуры">
        <i class="fa-solid fa-upload"></i>
        Импорт
      </button>
    </div>
    <div class="bot-name-block">
      <h3 style="cursor: pointer" @click="openSettings">
        {{ props.botInfo?.name || '' }}
      </h3>
      <i class="fa-solid fa-copy copy-icon" @click="copyBotId"></i>
    </div>
    <div class="overflow">
      <ul>
        <li
          v-for="node in filteredNodes"
          :key="node.id"
          class="step-item"
          @click="openNodeSettings(node)"
        >
          {{ node.data.name }}
        </li>
      </ul>
    </div>
    
    <!-- Модальное окно для импорта -->
    <div v-if="showImportModal" class="import-modal-overlay" @click="closeImportModal">
      <div class="import-modal-content" @click.stop>
        <div class="import-modal-header">
          <h3>Импорт структуры бота</h3>
          <button @click="closeImportModal" class="close-btn">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>
        <div class="import-modal-body">
          <BotImportDropzone 
            ref="importDropzone"
            @file-selected="handleFileSelected"
            @import-success="handleImportSuccess"
            @import-error="handleImportError"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, useTemplateRef } from 'vue';
import { useRouter } from 'vue-router';
import { SettingsIcon, DownloadIcon } from '@/components/icons';
import MasterPanel from '@/components/panels/masterPanel.vue';
import SimpleNodePanel from '@/components/panels/simpleNodePanel.vue';
import EmitterNodePanel from '@/components/panels/emitterNodePanel.vue';
import McpPrompt from '@/components/mcpPrompt.vue';
import BotImportDropzone from '@/components/BotImportDropzone.vue';
import { useBotsStore } from '@/stores';
import notyf from '@/plugins/notyf';

const props = defineProps({
  nodes: {
    type: Array,
    required: true,
  },
  botId: {
    type: String,
    required: true,
  },
  botInfo: {
    type: Object,
  },
});

const resizeBar = useTemplateRef('resize-bar');
const width = computed(() => resizeBar.value?.width);
defineExpose({ width });

const { setDrawer, setProps } = inject('drawer');
const botsStore = useBotsStore();

// Импорт и экспорт
const showImportModal = ref(false);
const importDropzone = ref();

const openNodeSettings = (node) => {
  const drawers = {
    simple: SimpleNodePanel,
    emitter: EmitterNodePanel,
  };

  setDrawer(drawers[node.type]);
  setProps({ node, botId: props.botId });
};

const openSettings = () => {
  setDrawer(MasterPanel);
  setProps({ botId: props.botId, botInfo: props.botInfo });
};

const openMcpPrompt = () => {
  setDrawer(McpPrompt);
  setProps({ botId: props.botId });
};

const router = useRouter();

const filteredNodes = computed(() => {
  return props.nodes.filter((node) => node.data?.name);
});

const goBack = () => {
  router.push('/bots');
};

const copyBotId = () => {
  navigator.clipboard.writeText(props.botId || '');
};

// Экспорт бота
const exportBot = async () => {
  try {
    const response = await botsStore.exportBot(props.botId);
    if (response) {
      notyf.success('Bot exported successfully');
    }
  } catch (error) {
    const errorMessage = error?.response?.data?.detail || error?.message || 'Ошибка при экспорте бота';
    notyf.error(errorMessage);
  }
};

// Импорт бота
const openImportModal = () => {
  showImportModal.value = true;
};

const closeImportModal = () => {
  showImportModal.value = false;
  importDropzone.value?.clearFile();
};

const handleFileSelected = async (file) => {
  // Для импорта внутри бота всегда заменяем структуру текущего бота
  try {
    await importDropzone.value.importBot(props.botId);
    closeImportModal();
    
    // Обновляем данные бота
    const refreshBotData = inject('refreshBotData');
    if (refreshBotData) {
      await refreshBotData();
    }
  } catch (error) {
    console.error('Import error:', error);
  }
};

const handleImportSuccess = (bot) => {
  notyf.success('Структура бота успешно обновлена!');
  
  // Обновляем данные бота
  const refreshBotData = inject('refreshBotData');
  if (refreshBotData) {
    refreshBotData();
  }
};

const handleImportError = (error) => {
  console.error('Import error:', error);
};
</script>

<style scoped>
.aside {
  background: rgba(49, 49, 49, 1);
  width: v-bind(width);
  display: flex;
  flex-direction: column;
  word-wrap: break-word;
  position: relative;
}

.overflow {
  overflow-y: auto;
}

h3 {
  box-sizing: border-box;
  padding: 13px 10px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

.aside ul {
  padding: 0;
}

.aside li {
  padding: 13px 20px;
  cursor: pointer;
  list-style-type: none;
  font-size: 12px;
  font-weight: 800;
}

.aside li:hover,
.aside li.active {
  background: #3e3e3e;
}

.btns-block {
  display: flex;
  justify-content: space-between;
  padding: 20px 10px;
}

.btns-block button {
  display: flex;
  align-items: center;
  gap: 5px;
}

.back-icon {
  width: 11px;
}

.settings-icon {
  width: 15px;
}

.panel-tabs-wrapper {
  padding: 0 20px;
  border-bottom: 1px solid rgba(116, 116, 116, 1);
}

.bot-name-block {
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(116, 116, 116, 1);
}

.copy-icon {
  cursor: pointer;
  color: #fff;
  opacity: 0.5;
  transition: opacity 0.2s ease;
  padding: 13px 10px 13px 0;
}

.copy-icon:hover {
  opacity: 1;
}

.import-export-block {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-bottom: 1px solid rgba(116, 116, 116, 1);
}

.import-export-block button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 12px;
  border: 1px solid rgba(116, 116, 116, 0.5);
  border-radius: 4px;
  background: rgba(60, 60, 60, 0.8);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.import-export-block button:hover {
  background: rgba(80, 80, 80, 0.9);
  border-color: rgba(116, 116, 116, 0.8);
}

.import-export-block .icon {
  width: 12px;
  height: 12px;
}

.import-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.import-modal-content {
  background: #2d2d2d;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.import-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid rgba(116, 116, 116, 0.3);
}

.import-modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.1rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(116, 116, 116, 0.3);
  color: #fff;
}

.import-modal-body {
  padding: 1rem;
}
</style>
