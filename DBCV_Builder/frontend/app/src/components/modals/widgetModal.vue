<template>
  <div class="modal-overlay" @click="tryOpenConfirmModal">
    <div :class="['modal', { 'full-screen': isFullScreen }]" @click.stop>
      <div class="modal-head">
        <div class="modal-name">
          {{ isEditMode ? 'Редактирование виджета' : 'Новый виджет' }}
        </div>
        <div class="modal-options">
          <button class="modal-full-screen" @click.prevent="toggleFullScreen">
            <FullScreenIcon v-if="!isFullScreen" />
            <SmallScreenIcon v-else />
          </button>
          <button class="modal-close" @click.prevent="tryOpenConfirmModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      <BaseCopyableId class="ignore-gap" v-if="isEditMode" :id="currentWidgetId" />
      <form @input="isSomethingChanged = true" @submit.prevent="handleClose()">
        <div class="form-top">
          <BaseInput
            v-model="formData.name"
            class="dark"
            inputClass="input"
            label="Название *"
            labelColor="#FFFFFF"
            required
            type="text"
            :error="v$.name.$error ? v$.name.$errors[0].$message : ''"
          />
          <BaseInput
            v-model="formData.description"
            class="dark"
            inputClass="input"
            label="Описание"
            labelColor="#FFFFFF"
            type="text"
          />
        </div>
        <BaseCodeEditor
          v-model="formData.body"
          :defaultHeight="600"
          :isCollapsed="activeEditor !== 'html'"
          :isResizable="true"
          label="HTML"
          :labelColor="getEditorLabelColor(formData.body)"
          language="html"
          @input="isSomethingChanged = true"
          @toggle="setActiveEditor('html')"
        />
        <BaseCodeEditor
          v-model="formData.js"
          :defaultHeight="600"
          :isCollapsed="activeEditor !== 'js'"
          :isResizable="true"
          label="JS"
          :labelColor="getEditorLabelColor(formData.js)"
          language="javascript"
          @input="isSomethingChanged = true"
          @toggle="setActiveEditor('js')"
        />
        <BaseCodeEditor
          v-model="formData.css"
          :defaultHeight="600"
          :isCollapsed="activeEditor !== 'css'"
          :isResizable="true"
          label="CSS"
          :labelColor="getEditorLabelColor(formData.css)"
          language="css"
          @input="isSomethingChanged = true"
          @toggle="setActiveEditor('css')"
        />
        <div class="modal-actions">
          <BaseButton
            v-if="isEditMode"
            size="medium"
            styleType="danger"
            type="button"
            @click="deleteWidget"
            style="margin-right: auto"
          >
            Удалить
          </BaseButton>
          <BaseCommand command="S" />
          <BaseButton
            v-if="isSomethingChanged"
            size="medium"
            styleType="secondary"
            type="button"
            @click="tryOpenConfirmModal"
          >
            Закрыть
          </BaseButton>
          <BaseButton size="medium" styleType="primary" type="submit">
            {{ isEditMode ? (isSomethingChanged ? 'Сохранить и закрыть' : 'Закрыть') : 'Создать' }}
          </BaseButton>
        </div>
      </form>
    </div>
  </div>
  <confirmModal
    v-if="isConfirmModalOpen"
    @close="closeConfirmModal"
    @confirm="handleClose"
    @close-main="closeModal"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { CloseIcon, FullScreenIcon, SmallScreenIcon } from '@/components/icons';
import confirmModal from '@/components/modals/confirmModal.vue';
import notyf from '@/plugins/notyf';
import { useWidgetsStore } from '@/stores';
import { defaultWidget, type WidgetFormData } from '@/types/component_types';
import { useFullScreen, useGeneratedEntityName, useKeyboardShortcuts } from '@/composables';
import { useVuelidate } from '@vuelidate/core';
import { widgetRules } from '@/plugins/vuelidate';

interface WidgetModalProps {
  isEditMode: boolean;
  formData: WidgetFormData;
  currentWidgetId: string | null;
}

const props = defineProps<WidgetModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const widgetsStore = useWidgetsStore();
const isSomethingChanged = ref(false);
const isConfirmModalOpen = ref(false);

const formData = ref({ ...defaultWidget, ...props.formData });

const v$ = useVuelidate(widgetRules, formData);

// Полноэкранный режим
const { isFullScreen, toggleFullScreen, resetFullScreen } = useFullScreen();

// Состояние для активного редактора
const activeEditor = ref('html');

// Функция установки активного редактора
const setActiveEditor = (editor: string) => {
  activeEditor.value = activeEditor.value === editor ? '' : editor;
};

// Функция закрытия модалки
const closeModal = () => {
  isSomethingChanged.value = false;
  resetFullScreen();
  emit('close');
};

// Функция открытия модалки подтверждения
const tryOpenConfirmModal = () => {
  if (isSomethingChanged.value) isConfirmModalOpen.value = true;
  else closeModal();
};

// Функция закрытия модалки подтверждения
const closeConfirmModal = () => {
  isConfirmModalOpen.value = false;
};

// Обработка результата подтверждения (сохр/не сохр)
const handleClose = async (shouldSave: boolean = false) => {
  const needToSave = shouldSave || isSomethingChanged.value;
  if (needToSave) {
    const isValid = await v$.value.$validate();
    if (!isValid) {
      notyf.error('Ошибка!');
      return;
    }
    await saveWidget();
  }
  closeModal();
};

// Функция сохранения/обновления виджета
const saveWidget = async (): Promise<void> => {
  if (props.isEditMode && props.currentWidgetId) {
    await updateWidget();
  } else {
    await createNewWidget();
  }
};

// Функция создания нового виджета
const createNewWidget = async (): Promise<void> => {
  const response = await widgetsStore.createWidget(formData.value);
  if (response) {
    notyf.success('Виджет создан!');
    closeModal();
  }
};

// Функция обновления существующего виджета
const updateWidget = async (): Promise<void> => {
  const response = await widgetsStore.updateWidget(props.currentWidgetId as string, formData.value);
  if (response) {
    notyf.success('Сохранено!');
    closeModal();
  }
};

// Удаления виджета
const deleteWidget = async () => {
  if (confirm('Вы уверены, что хотите удалить этот виджет?')) {
    const response = await widgetsStore.deleteWidget(props.currentWidgetId as string);
    if (response) {
      notyf.success('Виджет удален!');
      closeModal();
    }
  }
};

const getEditorLabelColor = (content: string) => {
  return content.trim() ? '#FFFFFF' : '#B3B3B3';
};

const { generateName } = useGeneratedEntityName();

onMounted(() => {
  if (!props.isEditMode) {
    formData.value.name = generateName('виджет');
    isSomethingChanged.value = true;
  }
});

// Использование горячих клавиш
useKeyboardShortcuts({
  onEscape: tryOpenConfirmModal,
  onSave: saveWidget,
});
</script>

<style scoped>
.modal-overlay {
  display: grid;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 30px 0;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.modal {
  max-width: 100%;
  width: 716px;
  display: grid;
  align-items: start;
  grid-template-rows: auto auto 1fr;
  gap: 10px;
  padding: 10px 15px;
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
}

.modal.full-screen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  border-radius: 0;
  border: none;
  z-index: 1000;
  overflow: auto;
}

.modal-head {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
}

.modal-name {
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
}

.modal-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px;
}

.modal-full-screen,
.modal-close {
  display: grid;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  transition-duration: 0.1s;
  transition-property: transform, background, box-shadow;
  transition-timing-function: linear;
}

.modal-full-screen:hover,
.modal-close:hover {
  background: #00000044;
}

.modal-full-screen:active,
.modal-close:active {
  background: #00000044;
  transform: translate(2px, 2px);
  box-shadow: none;
}

form {
  display: grid;
  gap: 10px;
}

.form-top {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin: 0;
}

.ignore-gap {
  margin-top: -10px;
}
</style>
