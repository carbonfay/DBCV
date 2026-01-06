<template>
  <div class="modal-overlay" @click="tryOpenConfirmModal">
    <div :class="['modal', { 'full-screen': isFullScreen }]" @click.stop>
      <div class="modal-head">
        <div class="modal-name">
          {{ isEditMode ? 'Редактирование канала' : 'Новый канал' }}
        </div>
        <div class="modal-options">
          <button class="modal-full-screen" v-if="isEditMode" @click.prevent="toggleFullScreen">
            <FullScreenIcon v-if="!isFullScreen" />
            <SmallScreenIcon v-else />
          </button>
          <button class="modal-close" @click.prevent="tryOpenConfirmModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      <BaseCopyableId class="ignore-gap" v-if="isEditMode" :id="currentChannelId" />
      <form @submit.prevent="() => handleClose()" @input="isSomethingChanged = true">
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
        <BaseCheckbox label-color="#fff" v-model="formData.is_public" class="custom-checkbox">
          Публичный канал
        </BaseCheckbox>
        <BaseSelectSearch
          v-model="formData.default_bot_id"
          :options="botsOptions"
          label="Выбрать агента"
          label-color="#fff"
          class="dark"
        />
        <BaseCodeEditor
          v-if="isEditMode"
          label="Переменные"
          v-model="formData.variables"
          language="json"
          :defaultHeight="150"
          @input="isSomethingChanged = true"
          :is-collapsed="false"
          :is-resizable="false"
        />
        <botSubscribers
          v-if="isEditMode"
          v-model="formData.subscribers"
          @input="isSomethingChanged = true"
        />
        <div class="modal-actions">
          <BaseCommand command="S" />
          <BaseButton
            styleType="secondary"
            size="medium"
            type="button"
            v-if="isSomethingChanged"
            @click="tryOpenConfirmModal"
            :disabled="isLoading"
          >
            Закрыть
          </BaseButton>
          <BaseButton
            styleType="secondary"
            size="medium"
            type="submit"
            :disabled="isLoading"
            style="max-height: 40px"
          >
            <BaseLoader v-if="isLoading" />
            <span v-else>
              {{
                isEditMode ? (isSomethingChanged ? 'Сохранить и закрыть' : 'Закрыть') : 'Создать'
              }}
            </span>
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
import { ref, computed, onMounted } from 'vue';
import { CloseIcon, FullScreenIcon, SmallScreenIcon } from '@/components/icons';
import notyf from '@/plugins/notyf';
import { useBotsStore, useChannelsStore } from '@/stores';
import confirmModal from '@/components/modals/confirmModal.vue';
import botSubscribers from '@/components/botSubscribers.vue';
import { defaultChannel, type ChannelFormData } from '@/types/component_types';
import type { User } from '@/types/store_types';
import { useVuelidate } from '@vuelidate/core';
import { channelRules } from '@/plugins/vuelidate';
import { useFullScreen, useGeneratedEntityName, useKeyboardShortcuts } from '@/composables';

interface ChannelModalProps {
  isEditMode: boolean;
  formData: ChannelFormData;
  currentChannelId: string | null;
}

const props = defineProps<ChannelModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const channelsStore = useChannelsStore();
const botsStore = useBotsStore();

const isSomethingChanged = ref(false);
const isConfirmModalOpen = ref(false);

const isLoading = ref(false);

const formData = ref({
  ...defaultChannel,
  ...props.formData,
});

const v$ = useVuelidate(channelRules, formData);

// Полноэкранный режим
const { isFullScreen, toggleFullScreen, resetFullScreen } = useFullScreen();

// Список дефолтных ботов
const botsOptions = computed(() => {
  const options = botsStore.bots.map((bot) => ({ label: bot.name, value: bot.id }));
  options.unshift({ label: '', value: '' });
  return options;
});

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

// Универсальная обработка сохранения и закрытия
const handleClose = async (shouldSave: boolean = false) => {
  const needToSave = shouldSave || isSomethingChanged.value;
  if (needToSave) {
    const isValid = await v$.value.$validate();
    if (!isValid) {
      notyf.error('Ошибка!');
      return;
    }
    await saveChannel();
  }
  closeModal();
};

const saveChannel = async () => {
  if (props.isEditMode && props.currentChannelId) {
    await updateChannel();
  } else {
    await createNewChannel();
  }
};

// Создание канала
const createNewChannel = async () => {
  isLoading.value = true;
  const response = await channelsStore.createChannel({
    name: formData.value.name,
    description: formData.value.description,
    is_public: formData.value.is_public,
    default_bot_id: formData.value.default_bot_id || null,
  });
  if (response) {
    notyf.success('Канал создан!');
    isLoading.value = false;
    closeModal();
  }
};

// Обновление канала
const updateChannel = async () => {
  isLoading.value = true;
  let parsedVariables = {};
  try {
    if (formData.value.variables) {
      parsedVariables = JSON.parse(formData.value.variables);
    }
  } catch {
    notyf.error('Неверный формат JSON в поле "Переменные".');
    return;
  }

  await updateSubscribers();

  const response = await channelsStore.updateChannel(props.currentChannelId as string, {
    ...formData.value,
    variables: {
      data: parsedVariables,
    },
  });
  if (response) {
    notyf.success('Канал обновлен!');
    isLoading.value = false;
    closeModal();
  }
};

// Обновление подписчиков
const initialSubscribers = ref(props.formData.subscribers || []);
const updateSubscribers = async () => {
  const newIds = formData.value.subscribers?.map((b: User) => b.id) || [];
  const oldIds = initialSubscribers.value?.map((b: User) => b.id) || [];
  const toSubscribe = newIds.filter((id) => !oldIds.includes(id));
  const toUnsubscribe = oldIds.filter((id) => !newIds.includes(id));

  if (toSubscribe.length > 0 && props.currentChannelId) {
    await channelsStore.subscribeToChannel(props.currentChannelId, toSubscribe);
  }
  if (toUnsubscribe.length > 0 && props.currentChannelId) {
    await channelsStore.unsubscribeToChannel(props.currentChannelId, toUnsubscribe);
  }
};

const { generateName } = useGeneratedEntityName();

onMounted(() => {
  if (!props.isEditMode) {
    formData.value.name = generateName('канал');
    isSomethingChanged.value = true;
  }
});

// Использование горячих клавиш
useKeyboardShortcuts({
  onEscape: tryOpenConfirmModal,
  onSave: saveChannel,
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
  grid-auto-flow: column;
  gap: 5px;
  justify-content: end;
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

.custom-textarea {
  gap: 10px;
}
</style>
