<template>
  <div class="pages-component">
    <div class="container">
      <sidebarMenu />
      <div class="content-block">
        <div class="card create-card" @click="openModal">
          <FileIcon class="icon" />
          <div class="text">
            <span>Новый агент</span>
            <span class="subtitle">Прототипирование и сборка</span>
          </div>
        </div>
        
        <!-- Импорт бота -->
        <div class="import-section">
          <BotImportDropzone 
            ref="importDropzone"
            @file-selected="handleFileSelected"
            @import-success="handleImportSuccess"
            @import-error="handleImportError"
          />
        </div>
        <BaseSortButtons
          v-model="sortOption"
          v-model:searchQuery="searchQuery"
          :isSearch="true"
          :options="sortOptions"
        />
        <BaseLoader v-if="isLoading" />
        <div v-else class="card-container">
          <div class="card" v-for="bot in sortedItems" :key="bot.id" @click="goToBot(bot.id)">
            <div class="channel-actions">
              <div class="channel-action">
                <EditIcon @click.stop="editBot(bot)" class="icon edit-icon" />
              </div>
              <div class="channel-action">
                <DownloadIcon @click.stop="exportBot(bot.id)" class="icon export-icon" />
              </div>
              <div class="channel-action">
                <TrashIcon @click.stop="deleteBot(bot.id)" class="icon" />
              </div>
            </div>
            <h3>{{ bot.name }}</h3>
            <div class="card-content">
              <span class="bot-description">{{ bot?.description }}</span>
              <span>Владелец: {{ bot.owner?.username || 'Неизвестно' }}</span>
              <div class="date-steps">
                <span>
                  {{
                    sortOption === 'newest'
                      ? `Создан ${formatDate(bot.created_at)}`
                      : `Изменен ${formatDate(bot.updated_at)}`
                  }}
                </span>
                <span class="steps-count">
                  <i class="fa-solid fa-shoe-prints fa-rotate-270"></i>
                  {{ bot.steps?.length || 0 }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <botModal
    v-if="isModalOpen"
    :isEditMode="isEditMode"
    :formData="formData"
    :currentBotId="currentBotId"
    @close="handleCloseModal"
  />
  
  <!-- Модальное окно для замены структуры бота -->
  <BotReplaceModal
    v-model:isOpen="isReplaceModalOpen"
    :fileData="selectedFileData"
    @confirm="handleReplaceConfirm"
    @cancel="handleReplaceCancel"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { EditIcon, FileIcon, TrashIcon, DownloadIcon } from '@/components/icons';
import { useBotsStore } from '@/stores';
import sidebarMenu from '@/components/sidebarMenu.vue';
import botModal from '@/components/modals/botModal.vue';
import BotImportDropzone from '@/components/BotImportDropzone.vue';
import BotReplaceModal from '@/components/modals/BotReplaceModal.vue';
import notyf from '@/plugins/notyf';
import { useModal, useSorting } from '@/composables';
import { storeToRefs } from 'pinia';
import type { Bot } from '@/types/store_types';
import { defaultBot, type BotFormData } from '@/types/component_types';
import { formatDate } from '@/helpers';

const router = useRouter();
const botsStore = useBotsStore();

const currentBotId = ref<string | null>(null);

const formData = ref<BotFormData>({ ...defaultBot });
const { bots } = storeToRefs(botsStore);

const isLoading = ref(true);

// Импорт ботов
const importDropzone = ref();
const isReplaceModalOpen = ref(false);
const selectedFileData = ref<any>(null);
const selectedFile = ref<File | null>(null);

const { isModalOpen, isEditMode, openModal, openEditModal, closeModal } = useModal();

const { sortOption, sortOptions, searchQuery, sortedItems, addRecentItem } = useSorting(
  () => bots.value,
  undefined,
  'bot'
);

// Редактирование бота
const editBot = (bot: Bot) => {
  openEditModal();
  formData.value.name = bot.name || '';
  formData.value.description = bot.description || '';
  currentBotId.value = bot.id;
};

// Закрытие модалки
const handleCloseModal = (): void => {
  closeModal();
  resetForm();
};

// Сброс формы
const resetForm = (): void => {
  formData.value = { ...defaultBot };
};

// Удаление бота
const deleteBot = async (botId: string) => {
  if (confirm('Вы уверены, что хотите удалить этого агента?')) {
    const response = await botsStore.deleteBot(botId);
    if (response) {
      notyf.success('Агент удален!');
    }
  }
};

// Экспорт бота
const exportBot = async (botId: string) => {
  try {
    const response = await botsStore.exportBot(botId);
    if (response) {
      notyf.success('Bot exported successfully');
    }
  } catch (error: any) {
    const errorMessage = error?.response?.data?.detail || error?.message || 'Ошибка при экспорте бота';
    notyf.error(errorMessage);
  }
};

// Обработка импорта ботов
const handleFileSelected = async (file: File) => {
  selectedFile.value = file;
  
  try {
    // Читаем содержимое файла для предпросмотра
    const text = await file.text();
    const fileData = JSON.parse(text);
    selectedFileData.value = fileData;
    
    // Спрашиваем пользователя, что делать с файлом
    const action = confirm(
      `Файл "${file.name}" загружен.\n\n` +
      `Нажмите OK для создания нового бота\n` +
      `Нажмите Отмена для замены структуры существующего бота`
    );
    
    if (action) {
      // Создание нового бота
      await importDropzone.value.importBot();
    } else {
      // Замена структуры существующего бота
      isReplaceModalOpen.value = true;
    }
  } catch (error) {
    notyf.error('Ошибка при чтении файла. Убедитесь, что это валидный JSON файл.');
  }
};

const handleImportSuccess = (bot: any) => {
  // Обновляем список ботов
  botsStore.readBots();
};

const handleImportError = (error: string) => {
  console.error('Import error:', error);
};

const handleReplaceConfirm = async (targetBotId: string) => {
  if (!selectedFile.value) return;
  
  try {
    await importDropzone.value.importBot(targetBotId);
    isReplaceModalOpen.value = false;
    selectedFileData.value = null;
    selectedFile.value = null;
  } catch (error) {
    console.error('Replace error:', error);
  }
};

const handleReplaceCancel = () => {
  isReplaceModalOpen.value = false;
  selectedFileData.value = null;
  selectedFile.value = null;
  importDropzone.value?.clearFile();
};

const goToBot = (id: string) => {
  const bot = bots.value.find((b) => b.id === id);
  if (bot) {
    addRecentItem(bot.id, bot.name || bot.id);
  }
  router.push({ path: `/bot/${id}` });
};

onMounted(async () => {
  await botsStore.readBots();
  isLoading.value = false;
});
</script>

<style src="@/assets/styles/pages.css"></style>

<style scoped>
.card h3 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

.bot-description {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 8px 0;
}

.card-content {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.date-steps {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  width: 100%;
}

.steps-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: white;
}

.edit-icon,
.export-icon {
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.channel-action:hover .edit-icon,
.channel-action:hover .export-icon {
  opacity: 1;
}

.import-section {
  margin-bottom: 2rem;
}
</style>
