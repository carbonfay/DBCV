<template>
  <div class="modal-overlay" @click="closeModal">
    <div class="modal" @click.stop>
      <div class="modal-head">
        <div class="modal-name">Выполнение запроса</div>
        <div class="modal-options">
          <button class="modal-close" @click.prevent="closeModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      
      <form @submit.prevent="executeRequest">
        <div class="request-info">
          <h3>{{ request?.name || 'Неизвестный запрос' }}</h3>
          <p><strong>URL:</strong> {{ request?.request_url }}</p>
          <p><strong>Метод:</strong> {{ request?.method?.toUpperCase() }}</p>
        </div>

        <BaseCodeEditor
          v-model="variables"
          :defaultHeight="200"
          :isCollapsed="false"
          :isResizable="true"
          label="Variables"
          labelColor="#FFFFFF"
          language="json"
        />

        <div class="execute-options">
          <label class="checkbox-label">
            <input 
              v-model="dryRun" 
              type="checkbox" 
              class="checkbox-input"
            />
            <span class="checkbox-text">Dry Run (только проверить подстановку переменных)</span>
          </label>
        </div>

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
            size="medium"
            styleType="secondary"
            type="button"
            @click="closeModal"
          >
            Закрыть
          </BaseButton>
          <BaseButton 
            size="medium" 
            styleType="primary" 
            type="submit"
            :disabled="isExecuting"
          >
            {{ isExecuting ? 'Выполняется...' : (dryRun ? 'Проверить подстановку' : 'Выполнить запрос') }}
          </BaseButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { CloseIcon } from '@/components/icons';
import { useRequestsStore } from '@/stores';
import notyf from '@/plugins/notyf';
import type { Request, RequestExecuteResponse } from '@/types/store_types';

interface RequestExecuteModalProps {
  request: Request | null;
}

const props = defineProps<RequestExecuteModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'result', result: RequestExecuteResponse): void;
}>();

const requestsStore = useRequestsStore();
const isExecuting = ref(false);
const executeResult = ref<RequestExecuteResponse | null>(null);
const dryRun = ref(false);

// Переменные по умолчанию
const variables = ref({
  channel: {},
  user: {},
  bot: {},
  session: {}
});

const closeModal = () => {
  executeResult.value = null;
  emit('close');
};

const executeRequest = async () => {
  if (!props.request?.id) {
    notyf.error('Невозможно выполнить запрос: ID не найден');
    return;
  }

  isExecuting.value = true;
  executeResult.value = null;

  try {
    const response = await requestsStore.executeRequest(
      props.request.id, 
      variables.value, 
      dryRun.value
    );
    
    if (response?.data) {
      executeResult.value = response.data;
      const action = dryRun.value ? 'проверка подстановки' : 'выполнение запроса';
      notyf.success(`${action} выполнена успешно!`);
      // Передаем результат в родительскую модалку
      emit('result', response.data);
    } else {
      notyf.error('Не удалось выполнить запрос');
    }
  } catch (error: any) {
    notyf.error('Ошибка при выполнении запроса: ' + (error.message || 'Неизвестная ошибка'));
    executeResult.value = {
      status: 0,
      statusText: 'Error',
      headers: {},
      data: null,
      responseTime: 0,
      success: false,
      error: error.message || 'Неизвестная ошибка'
    };
  } finally {
    isExecuting.value = false;
  }
};
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
  width: 800px;
  max-width: 100%;
  display: grid;
  align-items: start;
  grid-template-rows: auto 1fr;
  gap: 10px;
  padding: 10px 15px;
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
  max-height: 90vh;
  overflow-y: auto;
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
  grid-template-columns: repeat(1, 1fr);
  gap: 5px;
}

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

.modal-close:hover {
  background: #00000044;
}

.modal-close:active {
  background: #00000044;
  transform: translate(2px, 2px);
  box-shadow: none;
}

.request-info {
  background: #2a2a2a;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.request-info h3 {
  margin: 0 0 10px 0;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.request-info p {
  margin: 5px 0;
  color: #ccc;
  font-size: 12px;
}

.execute-options {
  margin: 15px 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  accent-color: #4caf50;
}

.checkbox-text {
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
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

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>
