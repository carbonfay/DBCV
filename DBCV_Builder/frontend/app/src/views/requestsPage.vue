<template>
  <div class="pages-component">
    <div class="container">
      <sidebarMenu />
      <div class="content-block">
        <div class="card create-card" @click="openModal">
          <FileIcon class="icon" />
          <div class="text">
            <span>Новый реквест</span>
            <span class="subtitle">Прототипирование</span>
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
            class="card"
            v-for="request in sortedItems"
            :key="request.id"
            @click.stop="editRequest(request)"
          >
            <h3>{{ request.name }}</h3>
            <span v-if="request.owner">Владелец: {{ request.owner?.username }}</span>
            <span>
              {{
                sortOption === 'newest'
                  ? `Создан ${formatDate(request.created_at)}`
                  : `Изменен ${formatDate(request.updated_at)}`
              }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <requestModal
    v-if="isModalOpen"
    :isEditMode="isEditMode"
    :formData="formData"
    :currentRequestId="currentRequestId"
    @close="handleCloseModal"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { FileIcon } from '@/components/icons';
import { useRequestsStore } from '@/stores';
import requestModal from '@/components/modals/requestModal.vue';
import sidebarMenu from '@/components/sidebarMenu.vue';
import { useModal, useSorting } from '@/composables';
import { storeToRefs } from 'pinia';
import type { Request } from '@/types/store_types';
import { defaultRequest, type RequestFormData } from '@/types/component_types';
import { formatDate } from '@/helpers';

const requestsStore = useRequestsStore();

const currentRequestId = ref<string | null>(null);

const formData = ref<RequestFormData>({ ...defaultRequest });
const { requests } = storeToRefs(requestsStore);

const isLoading = ref(true);

const { isModalOpen, isEditMode, openModal, openEditModal, closeModal } = useModal();

const { sortOption, sortOptions, searchQuery, sortedItems, addRecentItem } = useSorting(
  () => requests.value,
  undefined,
  'request'
);

// Редактирование реквеста
const editRequest = (request: Request) => {
  openEditModal();
  const { id, created_at, updated_at, ...editData } = request;
  Object.assign(formData.value, editData);
  currentRequestId.value = request.id;
  addRecentItem(request.id, request.name);
};

// Закрытие модалки
const handleCloseModal = (): void => {
  closeModal();
  resetForm();
};

// Сброс формы
const resetForm = (): void => {
  formData.value = { ...defaultRequest };
};

onMounted(async () => {
  await requestsStore.readRequests();
  isLoading.value = false;
});
</script>

<style src="@/assets/styles/pages.css"></style>
