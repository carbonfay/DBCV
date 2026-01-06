<template>
  <div class="pages-component">
    <div class="container">
      <sidebarMenu />
      <div class="content-block">
        <div class="card create-card" @click="openModal">
          <FileIcon class="icon" />
          <div class="text">
            <span>Новый канал</span>
            <span class="subtitle">Прототипирование и сборка</span>
          </div>
        </div>
        <BaseSortButtons
          v-model="sortOption"
          v-model:searchQuery="searchQuery"
          :isSearch="true"
          :options="sortOptions"
        />
        <BaseLoader v-if="isLoading" />
        <div v-else class="card-container">
          <div
            v-for="channel in sortedItems"
            :key="channel.id"
            class="card"
            @click="openChannel(channel)"
          >
            <div class="channel-actions">
              <div class="channel-action">
                <EditIcon class="icon edit-icon" @click.stop="editChannel(channel)" />
              </div>
              <div class="channel-action">
                <TrashIcon class="icon" @click.stop="deleteChannel(channel.id)" />
              </div>
            </div>
            <h3>{{ channel.name }}</h3>
            <div class="card-content">
              <span class="channel-description">{{ channel?.description }}</span>
              <span>Публичный: {{ channel.is_public ? 'Да' : 'Нет' }}</span>
              <span>Владелец: {{ channel.owner?.username }}</span>
              <div class="date-subscribers">
                <span>
                  {{
                    sortOption === 'newest'
                      ? `Создан ${formatDate(channel.created_at)}`
                      : `Изменен ${formatDate(channel.updated_at)}`
                  }}
                </span>
                <span class="subscribers-count">
                  <i class="fa-solid fa-cube"></i>
                  {{ channel.subscribers?.filter((sub) => sub.type === 'bot').length || 0 }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Блок чата -->
      <div v-if="selectedChannel" class="right-panel">
        <BaseResizeBar ref="resize-bar" :init-value="500" :max="1000" :min="400" position="left" />
        <chatView
          :key="selectedChannel.id"
          :channel="selectedChannel"
          @close="closeChat"
          @edit="editChannel"
        />
      </div>
    </div>
  </div>
  <channelModal
    v-if="isModalOpen"
    :isEditMode="isEditMode"
    :formData="formData"
    :currentChannelId="currentChannelId"
    @close="handleCloseModal"
  />
</template>

<script setup lang="ts">
import { ref, useTemplateRef, computed, onMounted } from 'vue';
import { EditIcon, FileIcon, TrashIcon } from '@/components/icons';
import { useBotsStore, useChannelsStore } from '@/stores';
import sidebarMenu from '@/components/sidebarMenu.vue';
import chatView from '@/components/chatView.vue';
import ChannelModal from '@/components/modals/channelModal.vue';
import notyf from '@/plugins/notyf';
import { useModal, useSorting } from '@/composables';
import { storeToRefs } from 'pinia';
import type { Channel } from '@/types/store_types';
import { defaultChannel, type ChannelFormData } from '@/types/component_types';
import { formatDate } from '@/helpers';

const channelsStore = useChannelsStore();
const botsStore = useBotsStore();

const { isModalOpen, isEditMode, openModal, openEditModal, closeModal } = useModal();
const currentChannelId = ref<string | null>(null);

const formData = ref<ChannelFormData>({ ...defaultChannel });
const { channels } = storeToRefs(channelsStore);

const isLoading = ref(true);

// Настройки шторки
const resizeBar = useTemplateRef<{ width: number }>('resize-bar');
const rightPanelWidth = computed<number | undefined>(() => resizeBar.value?.width);

onMounted(async () => {
  await channelsStore.readChannels();
  isLoading.value = false;
  if (botsStore.bots.length === 0) {
    botsStore.readBots();
  }
});

// Composable для сортировки
const { sortOption, sortOptions, searchQuery, sortedItems, addRecentItem } = useSorting(
  () => channels.value,
  undefined,
  'channel'
);

// Редактирование канала
const editChannel = async (channel: Channel) => {
  openEditModal();
  const { id, created_at, updated_at, owner, default_bot, ...editData } = channel;
  Object.assign(formData.value, {
    ...editData,
    variables: JSON.stringify(channel.variables?.data || {}, null, 2),
  });
  currentChannelId.value = channel.id;
};

// Закрытие модалки
const handleCloseModal = (): void => {
  closeModal();
  resetForm();
};

// Сброс формы
const resetForm = (): void => {
  formData.value = { ...defaultChannel };
};

// Удаление канала
const deleteChannel = async (channelId: string) => {
  if (confirm('Вы уверены, что хотите удалить этот канал?')) {
    const response = await channelsStore.deleteChannel(channelId);
    if (response) {
      notyf.success('Канал удален!');
    }
  }
};

// Открытие/закрытие канала/чата
const selectedChannel = ref<Channel | null>(null);

const openChannel = (channel: Channel) => {
  selectedChannel.value = channel;
  addRecentItem(channel.id, channel.name);
};

const closeChat = () => {
  selectedChannel.value = null;
};
</script>

<style src="@/assets/styles/pages.css"></style>

<style scoped>
.right-panel {
  width: v-bind(rightPanelWidth);
}

.card h3 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

.channel-description {
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

.date-subscribers {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  width: 100%;
}

.subscribers-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: white;
}

.channel-actions .edit-icon {
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.channel-action:hover .edit-icon {
  opacity: 1;
}
</style>
