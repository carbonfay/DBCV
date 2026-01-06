<template>
  <Teleport to="body">
    <div class="modal-overlay" @click="closeModal">
    <div class="modal" @click.stop>
      <div class="modal-head">
        <div class="modal-name">Выполнение шага</div>
        <div class="modal-options">
          <button class="modal-close" @click.prevent="closeModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      
      <form @submit.prevent="executeStep">
        <div class="step-info">
          <h3>{{ step?.name || 'Неизвестный шаг' }}</h3>
          <p v-if="step?.description"><strong>Описание:</strong> {{ step.description }}</p>
          <p v-if="step?.bot_id"><strong>Bot ID:</strong> {{ step.bot_id }}</p>
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

        <div class="input-group">
          <label class="input-label">
            Bot ID (опционально)
            <input 
              v-model="botId" 
              type="text" 
              class="input-field"
              placeholder="Оставьте пустым, чтобы использовать bot_id из шага"
            />
          </label>
        </div>

        <BaseCodeEditor
          v-model="context"
          :defaultHeight="150"
          :isCollapsed="false"
          :isResizable="true"
          label="Context"
          labelColor="#FFFFFF"
          language="json"
        />

        <!-- Результат выполнения шага -->
        <div v-if="executeResult" class="execute-result">
          <h4>Результаты выполнения:</h4>
          
          <!-- Список результатов групп -->
          <div v-if="executeResult.results && executeResult.results.length > 0" class="results-list">
            <div 
              v-for="(result, index) in executeResult.results" 
              :key="index"
              class="result-item"
            >
              <div class="result-header">
                <div class="result-title">
                  <strong>Группа {{ index + 1 }}:</strong> {{ result.group_id }}
                </div>
                <div class="result-meta">
                  <span class="result-type">Тип: {{ result.search_type }}</span>
                  <span class="result-priority">Приоритет: {{ result.priority }}</span>
                </div>
              </div>
              
              <div v-if="result.result !== null && result.result !== undefined" class="result-content">
                <BaseCodeEditor
                  :model-value="JSON.stringify(result.result, null, 2)"
                  :defaultHeight="150"
                  :isCollapsed="false"
                  :isResizable="true"
                  :label="`Результат группы ${index + 1}`"
                  labelColor="#FFFFFF"
                  language="json"
                  :readonly="true"
                />
              </div>
              
              <div v-if="result.variables_updated" class="result-variables">
                <strong>Обновленные переменные:</strong>
                <BaseCodeEditor
                  :model-value="JSON.stringify(result.variables_updated, null, 2)"
                  :defaultHeight="100"
                  :isCollapsed="false"
                  :isResizable="true"
                  label="Переменные"
                  labelColor="#FFFFFF"
                  language="json"
                  :readonly="true"
                />
              </div>
              
              <div v-if="result.result && result.result.error" class="error-message">
                Ошибка: {{ result.result.error }}
                <div v-if="result.result.traceback" class="traceback">
                  {{ result.result.traceback }}
                </div>
              </div>
            </div>
          </div>

          <!-- Финальные переменные -->
          <div v-if="executeResult.final_variables" class="final-variables">
            <h5>Финальные переменные:</h5>
            <BaseCodeEditor
              :model-value="JSON.stringify(executeResult.final_variables, null, 2)"
              :defaultHeight="200"
              :isCollapsed="false"
              :isResizable="true"
              label="Финальные переменные"
              labelColor="#FFFFFF"
              language="json"
              :readonly="true"
            />
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
            {{ isExecuting ? 'Выполняется...' : 'Выполнить шаг' }}
          </BaseButton>
        </div>
      </form>
    </div>
  </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, Teleport } from 'vue';
import { CloseIcon } from '@/components/icons';
import { useStepsStore } from '@/stores';
import notyf from '@/plugins/notyf';
import type { Step } from '@/types/store_types';
import BaseCodeEditor from '@/components/ui/BaseCodeEditor.vue';
import BaseButton from '@/components/ui/BaseButton.vue';

interface StepExecuteModalProps {
  step: Step | null;
}

const props = defineProps<StepExecuteModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const stepsStore = useStepsStore();
const isExecuting = ref(false);
const executeResult = ref<any>(null);
const botId = ref<string>('');

// Переменные по умолчанию
const variables = ref(JSON.stringify({
  channel: {},
  user: {},
  bot: {},
  session: {}
}, null, 2));

const context = ref(JSON.stringify({}, null, 2));

const closeModal = () => {
  executeResult.value = null;
  botId.value = '';
  variables.value = JSON.stringify({
    channel: {},
    user: {},
    bot: {},
    session: {}
  }, null, 2);
  context.value = JSON.stringify({}, null, 2);
  emit('close');
};

const executeStep = async () => {
  console.log('executeStep called', { step: props.step });
  
  if (!props.step) {
    notyf.error('Невозможно выполнить шаг: данные шага не найдены');
    return;
  }
  
  const stepId = props.step.id;
  if (!stepId) {
    notyf.error('Невозможно выполнить шаг: ID не найден');
    console.error('Step object:', props.step);
    return;
  }

  isExecuting.value = true;
  executeResult.value = null;

  try {
    // Парсим JSON из строк
    let variablesObj = {};
    let contextObj = {};
    
    try {
      variablesObj = JSON.parse(variables.value);
    } catch (e) {
      notyf.error('Ошибка в формате Variables JSON');
      isExecuting.value = false;
      return;
    }
    
    try {
      contextObj = JSON.parse(context.value);
    } catch (e) {
      notyf.error('Ошибка в формате Context JSON');
      isExecuting.value = false;
      return;
    }

    const requestData: any = {
      variables: variablesObj,
      context: contextObj
    };

    if (botId.value.trim()) {
      requestData.bot_id = botId.value.trim();
    }

    console.log('Calling runStep with:', { stepId, requestData });
    const response = await stepsStore.runStep(stepId, requestData);
    console.log('runStep response:', response);
    
    if (response?.data) {
      executeResult.value = response.data;
      notyf.success('Шаг выполнен успешно!');
    } else {
      notyf.error('Не удалось выполнить шаг');
    }
  } catch (error: any) {
    notyf.error('Ошибка при выполнении шага: ' + (error.message || 'Неизвестная ошибка'));
    executeResult.value = {
      results: [],
      final_variables: {},
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
  z-index: 9999;
}

.modal {
  width: 900px;
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

.step-info {
  background: #2a2a2a;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.step-info h3 {
  margin: 0 0 10px 0;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.step-info p {
  margin: 5px 0;
  color: #ccc;
  font-size: 12px;
}

.input-group {
  margin: 15px 0;
}

.input-label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}

.input-field {
  padding: 8px 12px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
}

.input-field:focus {
  outline: none;
  border-color: #4caf50;
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

.execute-result h5 {
  margin: 15px 0 10px 0;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.result-item {
  background: #1f1f1f;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #333;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 10px;
}

.result-title {
  color: #fff;
  font-size: 13px;
}

.result-meta {
  display: flex;
  gap: 15px;
  font-size: 11px;
  color: #aaa;
}

.result-content {
  margin-top: 10px;
}

.result-variables {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #333;
}

.result-variables strong {
  display: block;
  margin-bottom: 5px;
  color: #fff;
  font-size: 12px;
}

.final-variables {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid #444;
}

.error-message {
  margin-top: 10px;
  padding: 10px;
  background: #f44336;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
}

.traceback {
  margin-top: 10px;
  padding: 10px;
  background: #1a1a1a;
  border-radius: 4px;
  font-family: monospace;
  font-size: 11px;
  white-space: pre-wrap;
  overflow-x: auto;
}

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>

