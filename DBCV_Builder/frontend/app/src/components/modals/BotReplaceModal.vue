<template>
  <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Заменить структуру бота</h2>
        <button @click="closeModal" class="close-btn">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <div class="file-preview" v-if="fileData">
          <h3>Предпросмотр файла:</h3>
          <div class="preview-content">
            <div class="preview-item">
              <strong>Название:</strong> {{ fileData.name || 'Не указано' }}
            </div>
            <div class="preview-item">
              <strong>Описание:</strong> {{ fileData.description || 'Не указано' }}
            </div>
            <div class="preview-item" v-if="fileData.steps">
              <strong>Количество шагов:</strong> {{ fileData.steps.length }}
            </div>
          </div>
        </div>
        
        <div class="bot-selection">
          <label for="bot-select">Выберите бота для замены структуры:</label>
          <select 
            id="bot-select" 
            v-model="selectedBotId" 
            class="bot-select"
            :disabled="isLoading"
          >
            <option value="">-- Выберите бота --</option>
            <option 
              v-for="bot in bots" 
              :key="bot.id" 
              :value="bot.id"
            >
              {{ bot.name }} ({{ bot.steps?.length || 0 }} шагов)
            </option>
          </select>
        </div>
        
        <div class="warning" v-if="selectedBotId">
          <i class="fa-solid fa-exclamation-triangle"></i>
          <span>
            Внимание! Это действие заменит структуру выбранного бота. 
            Все существующие шаги и связи будут удалены.
          </span>
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          @click="closeModal" 
          class="btn btn-secondary"
          :disabled="isLoading"
        >
          Отмена
        </button>
        <button 
          @click="confirmReplace" 
          class="btn btn-primary"
          :disabled="!selectedBotId || isLoading"
        >
          <span v-if="isLoading" class="spinner-small"></span>
          {{ isLoading ? 'Замена...' : 'Заменить структуру' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useBotsStore } from '@/stores';
import { storeToRefs } from 'pinia';
import type { Bot } from '@/types/store_types';

interface Props {
  isOpen: boolean;
  fileData: any;
  onConfirm: (targetBotId: string) => void;
  onCancel: () => void;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:isOpen': [value: boolean];
  'confirm': [targetBotId: string];
  'cancel': [];
}>();

const botsStore = useBotsStore();
const { bots } = storeToRefs(botsStore);
const selectedBotId = ref<string>('');
const isLoading = ref(false);

const closeModal = () => {
  emit('update:isOpen', false);
  emit('cancel');
  selectedBotId.value = '';
};

const handleOverlayClick = () => {
  if (!isLoading.value) {
    closeModal();
  }
};

const confirmReplace = async () => {
  if (!selectedBotId.value) {
    return;
  }
  
  isLoading.value = true;
  try {
    emit('confirm', selectedBotId.value);
  } finally {
    isLoading.value = false;
  }
};

// Сброс выбора при закрытии модалки
watch(() => props.isOpen, (newValue) => {
  if (!newValue) {
    selectedBotId.value = '';
    isLoading.value = false;
  }
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.file-preview {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.file-preview h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-item {
  color: #555;
}

.preview-item strong {
  color: #333;
}

.bot-selection {
  margin-bottom: 1.5rem;
}

.bot-selection label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 500;
}

.bot-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
}

.bot-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.bot-select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.warning {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  color: #856404;
}

.warning i {
  color: #f39c12;
  margin-top: 0.125rem;
}

.warning span {
  flex: 1;
  line-height: 1.4;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #eee;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-primary {
  background: #dc3545;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #c82333;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
