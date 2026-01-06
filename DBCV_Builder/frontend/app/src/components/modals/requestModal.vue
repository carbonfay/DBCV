<template>
  <div class="modal-overlay" @click="tryOpenConfirmModal">
    <div :class="['modal', { 'full-screen': isFullScreen }]" @click.stop>
      <div class="modal-head">
        <div class="modal-name">
          {{ isEditMode ? 'Редактирование реквеста' : 'Новый реквест' }}
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
      <BaseCopyableId v-if="isEditMode" :id="currentRequestId" class="ignore-gap" />
      <form @input="isSomethingChanged = true" @submit.prevent="handleClose()">
        <div class="form-top">
          <BaseInput
            v-model="formData.name"
            class="dark"
            label="Название реквеста *"
            labelColor="#FFFFFF"
            :error="v$.name.$error ? v$.name.$errors[0].$message : ''"
          />
          <BaseSelect
            v-model="formData.method"
            :options="[
              { value: 'get', label: 'GET' },
              { value: 'post', label: 'POST' },
            ]"
            class="dark"
            label="Метод *"
            labelColor="#FFFFFF"
            :error="v$.method.$error ? v$.method.$errors[0].$message : ''"
          />
        </div>
        <BaseInput
          v-model="formData.request_url"
          class="dark"
          label="Request Url *"
          labelColor="#FFFFFF"
          :error="v$.request_url.$error ? v$.request_url.$errors[0].$message : ''"
        />
        <BaseInput v-model="formData.content" class="dark" label="Content" labelColor="#FFFFFF" />
        <BaseInput v-model="formData.headers" class="dark" label="Headers" labelColor="#FFFFFF" />
        <BaseInput
          v-model="formData.attachments"
          class="dark"
          label="Attachments"
          labelColor="#FFFFFF"
        />
        <BaseInput v-model="formData.proxies" class="dark" label="Proxies" labelColor="#FFFFFF" />
        <BaseCodeEditor
          v-model="formData.json_field"
          :defaultHeight="100"
          :isCollapsed="true"
          :isResizable="true"
          label="Json field"
          :labelColor="getEditorLabelColor(formData.json_field || '')"
          language="json"
          @input="isSomethingChanged = true"
        />
        <BaseCodeEditor
          v-model="formData.params"
          :defaultHeight="100"
          :isCollapsed="true"
          :isResizable="true"
          label="Параметры"
          :labelColor="getEditorLabelColor(formData.params)"
          language="json"
          @input="isSomethingChanged = true"
        />
        <BaseCodeEditor
          v-model="formData.data"
          :defaultHeight="100"
          :isCollapsed="true"
          :isResizable="true"
          label="Data"
          :labelColor="getEditorLabelColor(formData.data)"
          language="json"
          @input="isSomethingChanged = true"
        />
        <BaseCodeEditor
          v-model="formData.url_params"
          :defaultHeight="100"
          :isCollapsed="true"
          :isResizable="true"
          label="Url Params"
          :labelColor="getEditorLabelColor(formData.url_params)"
          language="json"
          @input="isSomethingChanged = true"
        />
        
        <!-- Результат выполнения запроса -->
        <div v-if="executeResult" class="execute-result">
          <h4>Результат выполнения запроса:</h4>
          <div class="result-info">
            <div class="result-status" :class="{ 'success': executeResult.success, 'error': !executeResult.success }">
              Статус: {{ executeResult.status }} {{ executeResult.statusText }}
            </div>
            <div class="result-time">Время выполнения: {{ executeResult.responseTime }}мс</div>
          </div>
          <BaseCodeEditor
            :model-value="JSON.stringify(executeResult.data, null, 2)"
            :defaultHeight="200"
            :isCollapsed="false"
            :isResizable="true"
            label="Ответ"
            labelColor="#FFFFFF"
            language="json"
            :readonly="true"
          />
          <div v-if="executeResult.error" class="error-message">
            Ошибка: {{ executeResult.error }}
          </div>
        </div>

        <div class="modal-actions">
          <BaseButton
            v-if="isEditMode"
            size="medium"
            styleType="danger"
            type="button"
            @click="deleteRequest"
            style="margin-right: auto"
          >
            Удалить
          </BaseButton>
          <BaseButton
            v-if="isEditMode"
            size="medium"
            styleType="success"
            type="button"
            @click="openExecuteModal"
            style="margin-right: auto"
          >
            Execute
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
  <requestExecuteModal
    v-if="isExecuteModalOpen"
    :request="currentRequest"
    @close="closeExecuteModal"
    @result="handleExecuteResult"
  />
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { CloseIcon, FullScreenIcon, SmallScreenIcon } from '@/components/icons';
import confirmModal from '@/components/modals/confirmModal.vue';
import requestExecuteModal from '@/components/modals/requestExecuteModal.vue';
import notyf from '@/plugins/notyf';
import { useRequestsStore } from '@/stores';
import { defaultRequest, type RequestFormData } from '@/types/component_types';
import { useVuelidate } from '@vuelidate/core';
import { requestRules } from '@/plugins/vuelidate';
import { useFullScreen, useGeneratedEntityName, useKeyboardShortcuts } from '@/composables';
import type { Request, RequestExecuteResponse } from '@/types/store_types';

interface RequestModalProps {
  isEditMode: boolean;
  formData: RequestFormData;
  currentRequestId: string | null;
}

const props = defineProps<RequestModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const requestsStore = useRequestsStore();
const isSomethingChanged = ref(false);
const isConfirmModalOpen = ref(false);
const isExecuteModalOpen = ref(false);
const executeResult = ref<RequestExecuteResponse | null>(null);

const formData = ref({ ...defaultRequest, ...props.formData });

// Текущий реквест для выполнения
const currentRequest = computed(() => {
  if (!props.currentRequestId) return null;
  return requestsStore.requests.find(req => req.id === props.currentRequestId) || null;
});

const v$ = useVuelidate(requestRules, formData);

// Полноэкранный режим
const { isFullScreen, toggleFullScreen, resetFullScreen } = useFullScreen();

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
    await saveRequest();
  }
  closeModal();
};

// Функция сохранения/обновления реквеста
const saveRequest = async (): Promise<void> => {
  if (props.isEditMode && props.currentRequestId) {
    await updateRequest();
  } else {
    await createNewRequest();
  }
};

// Отправка null вместо пустых строк
const prepareFormData = (data: RequestFormData): Record<string, unknown> => {
  return Object.fromEntries(
    Object.entries(data).map(([key, value]) => [key, value === '' ? null : value])
  );
};

// Создание реквеста
const createNewRequest = async (): Promise<void> => {
  const preparedData = prepareFormData(formData.value);
  const response = await requestsStore.createRequest(preparedData);
  if (response) {
    notyf.success('Реквест создан!');
    closeModal();
  }
};

// Обновление реквеста
const updateRequest = async (): Promise<void> => {
  const preparedData = prepareFormData(formData.value);
  const response = await requestsStore.updateRequest(
    props.currentRequestId as string,
    preparedData
  );
  if (response) {
    notyf.success('Сохранено!');
    closeModal();
  }
};

// Удаление реквеста
const deleteRequest = async () => {
  if (confirm('Вы уверены, что хотите удалить этот реквест?')) {
    const response = await requestsStore.deleteRequest(props.currentRequestId as string);
    if (response) {
      notyf.success('Реквест удален!');
      closeModal();
    }
  }
};

// Открытие модалки выполнения
const openExecuteModal = () => {
  isExecuteModalOpen.value = true;
};

// Закрытие модалки выполнения
const closeExecuteModal = () => {
  isExecuteModalOpen.value = false;
};

// Обработка результата выполнения
const handleExecuteResult = (result: RequestExecuteResponse) => {
  executeResult.value = result;
};

const getEditorLabelColor = (
  content: string | Record<string, unknown> | null | undefined
): string => {
  if (
    (typeof content === 'string' && content.trim()) ||
    (typeof content === 'object' &&
      content &&
      Object.keys(content as Record<string, unknown>).length)
  ) {
    return '#FFFFFF';
  }

  return '#B3B3B3';
};

const { generateName } = useGeneratedEntityName();

onMounted(() => {
  if (!props.isEditMode) {
    formData.value.name = generateName('реквест');
    isSomethingChanged.value = true;
  }
});

// Использование горячих клавиш
useKeyboardShortcuts({
  onEscape: tryOpenConfirmModal,
  onSave: saveRequest,
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

.execute-result {
  margin-top: 20px;
  padding: 15px;
  background: #2a2a2a;
  border-radius: 8px;
  border: 1px solid #444;
}

.execute-result h4 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.result-info {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.result-status {
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.result-status.success {
  background: #4caf50;
  color: #fff;
}

.result-status.error {
  background: #f44336;
  color: #fff;
}

.result-time {
  color: #ccc;
  font-size: 12px;
  display: flex;
  align-items: center;
}

.error-message {
  margin-top: 10px;
  padding: 10px;
  background: #f44336;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
}

</style>
