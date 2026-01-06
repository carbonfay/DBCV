<template>
  <div class="pages-component">
    <div class="container">
      <sidebarMenu />
      <div class="content-block">
        <div class="card create-card" @click="openModal">
          <FileIcon class="icon" />
          <div class="text">
            <span>Новый виджет</span>
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
            v-for="widget in sortedItems"
            :key="widget.id"
            @click.stop="editWidget(widget)"
          >
            <h3>{{ widget.name }}</h3>
            <span v-if="widget.description">Описание: {{ widget.description }}</span>
            <span>
              {{
                sortOption === 'newest'
                  ? `Создан ${formatDate(widget.created_at)}`
                  : `Изменен ${formatDate(widget.updated_at)}`
              }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <widgetModal
    v-if="isModalOpen"
    :isEditMode="isEditMode"
    :formData="formData"
    :currentWidgetId="currentWidgetId"
    @close="handleCloseModal"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { FileIcon } from '@/components/icons';
import { useWidgetsStore } from '@/stores';
import widgetModal from '@/components/modals/widgetModal.vue';
import sidebarMenu from '@/components/sidebarMenu.vue';
import { useModal, useSorting } from '@/composables';
import { storeToRefs } from 'pinia';
import type { Widget } from '@/types/store_types';
import { defaultWidget, type WidgetFormData } from '@/types/component_types';
import { formatDate } from '@/helpers';

const widgetsStore = useWidgetsStore();

const currentWidgetId = ref<string | null>(null);

const formData = ref<WidgetFormData>({ ...defaultWidget });
const { widgets } = storeToRefs(widgetsStore);

const isLoading = ref(true);

const { isModalOpen, isEditMode, openModal, openEditModal, closeModal } = useModal();

const { sortOption, sortOptions, searchQuery, sortedItems, addRecentItem } = useSorting(
  () => widgets.value,
  undefined,
  'widget'
);

// Редактирование виджета
const editWidget = (widget: Widget) => {
  openEditModal();
  const { id, created_at, updated_at, ...editData } = widget;
  Object.assign(formData.value, editData);
  currentWidgetId.value = widget.id;
  addRecentItem(widget.id, widget.name);
};

// Закрытие модалки
const handleCloseModal = (): void => {
  closeModal();
  resetForm();
};

// Сброс формы
const resetForm = (): void => {
  formData.value = { ...defaultWidget };
};

onMounted(async () => {
  await widgetsStore.readWidgets();
  isLoading.value = false;
});
</script>

<style src="@/assets/styles/pages.css"></style>
