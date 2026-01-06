<template>
  <div
    class="import-dropzone"
    :class="{ 'drag-over': isDragOver, 'loading': isLoading }"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
    @click="triggerFileInput"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".json"
      @change="handleFileSelect"
      style="display: none"
    />
    
    <div v-if="isLoading" class="loading-content">
      <div class="spinner"></div>
      <p>Импорт бота...</p>
    </div>
    
    <div v-else class="dropzone-content">
      <div class="icon">
        <i class="fa-solid fa-cloud-upload-alt"></i>
      </div>
      <h3>Импорт бота</h3>
      <p>Перетащите JSON файл сюда или нажмите для выбора файла</p>
      <div class="file-info" v-if="selectedFile">
        <p><strong>Выбранный файл:</strong> {{ selectedFile.name }}</p>
        <button @click.stop="clearFile" class="clear-btn">Очистить</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useBotsStore } from '@/stores';
import notyf from '@/plugins/notyf';

interface Props {
  onImportSuccess?: (bot: any) => void;
  onImportError?: (error: string) => void;
}

const props = withDefaults(defineProps<Props>(), {
  onImportSuccess: () => {},
  onImportError: () => {},
});

const emit = defineEmits<{
  'import-success': [bot: any];
  'import-error': [error: string];
  'file-selected': [file: File];
}>();

const botsStore = useBotsStore();
const fileInput = ref<HTMLInputElement>();
const isDragOver = ref(false);
const isLoading = ref(false);
const selectedFile = ref<File | null>(null);

const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;
  
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (validateFile(file)) {
      selectedFile.value = file;
      emit('file-selected', file);
    }
  }
};

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const files = target.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (validateFile(file)) {
      selectedFile.value = file;
      emit('file-selected', file);
    }
  }
};

const validateFile = (file: File): boolean => {
  if (!file.name.toLowerCase().endsWith('.json')) {
    notyf.error('Пожалуйста, выберите JSON файл');
    return false;
  }
  
  if (file.size > 10 * 1024 * 1024) { // 10MB limit
    notyf.error('Размер файла не должен превышать 10MB');
    return false;
  }
  
  return true;
};

const clearFile = () => {
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const importBot = async (targetBotId?: string) => {
  if (!selectedFile.value) {
    notyf.error('Пожалуйста, выберите файл для импорта');
    return;
  }
  
  isLoading.value = true;
  
  try {
    const response = await botsStore.importBot(selectedFile.value, targetBotId);
    
    if (response) {
      notyf.success(targetBotId ? 'Структура бота обновлена!' : 'Бот успешно импортирован!');
      emit('import-success', response.data);
      clearFile();
    }
  } catch (error: any) {
    const errorMessage = error?.response?.data?.detail || error?.message || 'Ошибка при импорте бота';
    notyf.error(errorMessage);
    emit('import-error', errorMessage);
  } finally {
    isLoading.value = false;
  }
};

// Экспонируем метод для использования в родительском компоненте
defineExpose({
  importBot,
  clearFile,
  selectedFile: selectedFile.value,
});
</script>

<style scoped>
.import-dropzone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f9f9f9;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.import-dropzone:hover {
  border-color: #007bff;
  background: #f0f8ff;
}

.import-dropzone.drag-over {
  border-color: #007bff;
  background: #e3f2fd;
  transform: scale(1.02);
}

.import-dropzone.loading {
  cursor: not-allowed;
  opacity: 0.7;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.icon {
  font-size: 3rem;
  color: #007bff;
  margin-bottom: 0.5rem;
}

.icon i {
  font-size: inherit;
}

h3 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

p {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.file-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #e8f5e8;
  border-radius: 4px;
  border: 1px solid #4caf50;
}

.file-info p {
  color: #2e7d32;
  font-weight: 500;
}

.clear-btn {
  background: #ff4444;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s ease;
}

.clear-btn:hover {
  background: #d32f2f;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-content p {
  color: #007bff;
  font-weight: 500;
}
</style>
