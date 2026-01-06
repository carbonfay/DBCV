<template>
  <div class="modal-overlay" @click="tryOpenConfirmModal">
    <div :class="'modal'" @click.stop>
      <div class="modal-head">
        <div class="modal-name">
          {{ isEditMode ? 'Редактирование агента' : 'Новый агент' }}
        </div>
        <div class="modal-options">
          <button class="modal-close" @click.prevent="tryOpenConfirmModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      <BaseCopyableId class="ignore-gap" v-if="isEditMode" :id="currentBotId" />
      <form @submit.prevent="handleClose()" @input="isSomethingChanged = true">
        <div class="form-top">
          <BaseInput
            type="text"
            required
            v-model="formData.name"
            label="Название *"
            labelColor="#FFFFFF"
            inputClass="input"
            class="dark"
            :error="v$.name.$error ? v$.name.$errors[0].$message : ''"
          />
        </div>
        <BaseTextarea
          v-model="formData.description"
          class="custom-textarea"
          :textColor="'#ffffff'"
          :backgroundColor="'#212121'"
          :border="'none'"
          :label="'Описание'"
        />
        <div class="modal-actions">
          <BaseCommand command="S" />
          <BaseButton
            styleType="secondary"
            size="medium"
            type="button"
            v-if="isSomethingChanged"
            @click="tryOpenConfirmModal"
          >
            Закрыть
          </BaseButton>
          <BaseButton styleType="primary" size="medium" type="submit">
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
import notyf from '@/plugins/notyf';
import { useBotsStore } from '@/stores';
import confirmModal from '@/components/modals/confirmModal.vue';
import { defaultBot, type BotFormData } from '@/types/component_types';
import { useVuelidate } from '@vuelidate/core';
import { botRules } from '@/plugins/vuelidate';
import { useGeneratedEntityName, useKeyboardShortcuts } from '@/composables';

interface BotModalProps {
  isEditMode: boolean;
  formData: BotFormData;
  currentBotId: string | null;
}

const props = defineProps<BotModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const botsStore = useBotsStore();
const isSomethingChanged = ref(false);
const isConfirmModalOpen = ref(false);

const formData = ref({
  ...defaultBot,
  ...props.formData,
});

const v$ = useVuelidate(botRules, formData);

// Функция закрытия модалки
const closeModal = () => {
  isSomethingChanged.value = false;
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
    await saveBot();
  }
  closeModal();
};

// Функция сохранения/обновления бота
const saveBot = async (): Promise<void> => {
  if (props.isEditMode && props.currentBotId) {
    await updateBot();
  } else {
    await createNewBot();
  }
};

// Создание нового бота
const createNewBot = async (): Promise<void> => {
  const response = await botsStore.createBot(formData.value);
  if (response) {
    notyf.success('Агент создан!');
    closeModal();
  }
};

// Обновление бота
const updateBot = async (): Promise<void> => {
  const response = await botsStore.updateBot(props.currentBotId as string, formData.value);
  if (response) {
    notyf.success('Сохранено!');
    closeModal();
  }
};

const { generateName } = useGeneratedEntityName();

onMounted(() => {
  if (!props.isEditMode) {
    formData.value.name = generateName('агент');
    isSomethingChanged.value = true;
  }
});

// Инициализация keyboard shortcuts
useKeyboardShortcuts({
  onEscape: tryOpenConfirmModal,
  onSave: handleClose,
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
  width: 716px;
  max-width: 100%;
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
