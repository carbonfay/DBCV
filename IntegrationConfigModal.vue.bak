<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal" @click.stop>
      <div class="modal-head">
        <div class="modal-name">{{ integration?.name || 'Настройка интеграции' }}</div>
        <button class="modal-close" @click="handleClose">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="integration?.description" class="integration-description">
          {{ integration.description }}
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div
            v-for="field in formFields"
            :key="field.key"
            class="form-field"
          >
            <BaseInput
              v-if="field.type === 'string' && !field.enum"
              v-model="formData[field.key]"
              :label="field.title + (field.required ? ' *' : '')"
              :placeholder="field.description || field.title"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
              <BaseSelect
                v-else-if="field.type === 'string' && field.enum"
                v-model="formData[field.key]"
                :options="field.enum.map((v: any) => ({ value: v, label: v }))"
              :label="field.title + (field.required ? ' *' : '')"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
            <BaseInput
              v-else-if="field.type === 'number' || field.type === 'integer'"
              v-model.number="formData[field.key]"
              type="number"
              :label="field.title + (field.required ? ' *' : '')"
              :placeholder="field.description || field.title"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
            <BaseCheckbox
              v-else-if="field.type === 'boolean'"
              v-model="formData[field.key]"
              :label="field.title + (field.required ? ' *' : '')"
            />
            
            <!-- Array поле - JSON редактор -->
            <div v-else-if="field.type === 'array'" class="json-field">
              <label class="field-label">
                {{ field.title + (field.required ? ' *' : '') }}
              </label>
              <textarea
                v-model="formDataJson[field.key]"
                class="json-editor"
                :placeholder="field.description || 'JSON массив, например: [1, 2, 3]'"
                @input="handleJsonInput(field.key)"
              />
              <small class="field-hint">{{ field.description || 'Введите JSON массив' }}</small>
              <div v-if="errors[field.key]" class="error-message">{{ errors[field.key] }}</div>
            </div>
            
            <!-- Object поле - JSON редактор -->
            <div v-else-if="field.type === 'object'" class="json-field">
              <label class="field-label">
                {{ field.title + (field.required ? ' *' : '') }}
              </label>
              <textarea
                v-model="formDataJson[field.key]"
                class="json-editor"
                :placeholder="field.description || 'JSON объект, например: {&quot;key&quot;: &quot;value&quot;}'"
                @input="handleJsonInput(field.key)"
              />
              <small class="field-hint">{{ field.description || 'Введите JSON объект' }}</small>
              <div v-if="errors[field.key]" class="error-message">{{ errors[field.key] }}</div>
            </div>
          </div>
          
          <div v-if="integration?.examples && integration.examples.length > 0" class="examples-section">
            <h4>Примеры:</h4>
            <div
              v-for="(example, idx) in integration.examples"
              :key="idx"
              class="example-item"
              @click="loadExample(example.config)"
            >
              <strong>{{ example.title }}</strong>
              <pre>{{ JSON.stringify(example.config, null, 2) }}</pre>
            </div>
          </div>
          
          <div class="modal-actions">
            <BaseButton @click="handleClose" type="button">Отмена</BaseButton>
            <BaseButton type="submit" :disabled="isSubmitting">
              {{ isSubmitting ? 'Создание...' : 'Создать шаг' }}
            </BaseButton>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import BaseInput from '@/components/ui/BaseInput.vue';
import BaseSelect from '@/components/ui/BaseSelect.vue';
import BaseCheckbox from '@/components/ui/BaseCheckbox.vue';
import BaseButton from '@/components/ui/BaseButton.vue';
import stepsApi from '@/api/services/stepsApi';
import connectionGroupsApi from '@/api/services/connectionGroupsApi';
import notyf from '@/plugins/notyf';

const props = defineProps<{
  integration: any;
  botId: string;
  nextStepId?: string;
}>();

const emit = defineEmits(['close', 'created']);

const formData = ref<Record<string, any>>({});
const formDataJson = ref<Record<string, string>>({});
const errors = ref<Record<string, string>>({});
const isSubmitting = ref(false);

const formFields = computed(() => {
  if (!props.integration?.config_schema?.properties) return [];
  
  const schema = props.integration.config_schema;
  const required = schema.required || [];
  
  return Object.entries(schema.properties).map(([key, prop]: [string, any]) => ({
    key,
    title: prop.title || key,
    description: prop.description,
    type: prop.type,
    enum: prop.enum,
    format: prop.format,
    required: required.includes(key),
    default: prop.default,
  }));
});

watch(
  () => props.integration,
  (integration) => {
    if (integration?.config_schema?.properties) {
      const schema = integration.config_schema;
      const initialData: Record<string, any> = {};
      const initialJson: Record<string, string> = {};
      
      Object.entries(schema.properties).forEach(([key, prop]: [string, any]) => {
        if (prop.default !== undefined) {
          initialData[key] = prop.default;
          
          // Для object и array типов инициализируем JSON строку
          if (prop.type === 'object' || prop.type === 'array') {
            initialJson[key] = JSON.stringify(prop.default, null, 2);
          }
        } else if (prop.type === 'object') {
          initialData[key] = {};
          initialJson[key] = '{}';
        } else if (prop.type === 'array') {
          initialData[key] = [];
          initialJson[key] = '[]';
        }
      });
      
      formData.value = initialData;
      formDataJson.value = initialJson;
    }
  },
  { immediate: true }
);

const handleJsonInput = (key: string) => {
  const jsonString = formDataJson.value[key] || '';
  errors.value[key] = '';
  
  if (!jsonString.trim()) {
    // Если пустая строка, очищаем ошибку
    delete errors.value[key];
    const field = formFields.value.find(f => f.key === key);
    if (field?.type === 'object') {
      formData.value[key] = {};
    } else if (field?.type === 'array') {
      formData.value[key] = [];
    }
    return;
  }
  
  try {
    const parsed = JSON.parse(jsonString);
    
    // Проверяем тип
    const field = formFields.value.find(f => f.key === key);
    if (field?.type === 'array' && !Array.isArray(parsed)) {
      errors.value[key] = 'Должен быть массив';
      return;
    }
    if (field?.type === 'object' && (Array.isArray(parsed) || typeof parsed !== 'object')) {
      errors.value[key] = 'Должен быть объект';
      return;
    }
    
    formData.value[key] = parsed;
    delete errors.value[key];
  } catch (e) {
    errors.value[key] = 'Некорректный JSON';
  }
};

const validateForm = () => {
  errors.value = {};
  let isValid = true;
  
  if (!props.integration?.config_schema?.required) return isValid;
  
  props.integration.config_schema.required.forEach((key: string) => {
    const prop = props.integration.config_schema.properties[key];
    const value = formData.value[key];
    
    // Для object и array типов проверяем, что JSON валидный
    if (prop?.type === 'object' || prop?.type === 'array') {
      const jsonString = formDataJson.value[key] || '';
      if (!jsonString.trim()) {
        errors.value[key] = 'Это поле обязательно';
        isValid = false;
        return;
      }
      try {
        const parsed = JSON.parse(jsonString);
        if (prop.type === 'array' && !Array.isArray(parsed)) {
          errors.value[key] = 'Должен быть массив';
          isValid = false;
          return;
        }
        if (prop.type === 'object' && (Array.isArray(parsed) || typeof parsed !== 'object')) {
          errors.value[key] = 'Должен быть объект';
          isValid = false;
          return;
        }
        // Синхронизируем formData
        formData.value[key] = parsed;
      } catch (e) {
        errors.value[key] = 'Некорректный JSON';
        isValid = false;
        return;
      }
    } else {
      // Для остальных типов
      if (value === undefined || value === null || value === '') {
        errors.value[key] = 'Это поле обязательно';
        isValid = false;
        return;
      }
      
      // Дополнительная валидация для UUID
      if (prop?.format === 'uuid') {
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (value && !uuidRegex.test(value)) {
          errors.value[key] = 'Некорректный формат UUID';
          isValid = false;
          return;
        }
      }
    }
  });
  
  return isValid;
};

const loadExample = (exampleConfig: Record<string, any>) => {
  // Обновляем formData
  formData.value = { ...formData.value, ...exampleConfig };
  
  // Обновляем JSON поля для всех object и array типов
  if (props.integration?.config_schema?.properties) {
    Object.entries(props.integration.config_schema.properties).forEach(([key, prop]: [string, any]) => {
      if (prop.type === 'object' || prop.type === 'array') {
        const value = exampleConfig[key] !== undefined ? exampleConfig[key] : formData.value[key];
        if (value !== undefined) {
          formDataJson.value[key] = JSON.stringify(value, null, 2);
          formData.value[key] = value;
        }
      }
    });
  }
};

const handleSubmit = async () => {
  if (!validateForm()) {
    notyf.error('Пожалуйста, заполните все обязательные поля');
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // 1. Создаем шаг
    const stepResponse = await stepsApi.createStep({
      bot_id: props.botId,
      name: props.integration.name,
      is_proxy: true,
      description: props.integration.description,
    });
    
    if (!stepResponse?.data) {
      throw new Error('Не удалось создать шаг');
    }
    
    const stepId = stepResponse.data.id;
    
    // 2. Создаем connection group с интеграцией
    const connectionGroupData: any = {
      step_id: stepId,
      search_type: 'integration',
      integration_id: props.integration.id,
      integration_config: formData.value,
      connections: [],
    };
    
    if (props.nextStepId) {
      connectionGroupData.connections.push({
        next_step_id: props.nextStepId,
        priority: 0,
        rules: null,
      });
    }
    
    const connectionGroupResponse = await connectionGroupsApi.createConnectionGroup(connectionGroupData);
    
    if (!connectionGroupResponse?.data) {
      throw new Error('Не удалось создать connection group');
    }
    
    notyf.success('Шаг с интеграцией успешно создан');
    emit('created', { step: stepResponse.data, connectionGroup: connectionGroupResponse.data });
    handleClose();
  } catch (error: any) {
    console.error('Error creating integration step:', error);
    const errorMessage = error?.response?.data?.detail || error?.message || 'Ошибка при создании шага';
    notyf.error(errorMessage);
  } finally {
    isSubmitting.value = false;
  }
};

const handleClose = () => {
  emit('close');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #2d2d2d;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid rgba(116, 116, 116, 0.3);
}

.modal-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
}

.modal-close {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(116, 116, 116, 0.3);
  color: #fff;
}

.modal-body {
  padding: 1.5rem;
}

.integration-description {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(60, 60, 60, 0.5);
  border-radius: 4px;
  color: #aaa;
  font-size: 0.9rem;
}

.form-field {
  margin-bottom: 1rem;
}

.examples-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(116, 116, 116, 0.3);
}

.examples-section h4 {
  margin: 0 0 1rem 0;
  color: #fff;
  font-size: 1rem;
}

.example-item {
  margin-bottom: 1rem;
  padding: 1rem;
  background: rgba(60, 60, 60, 0.5);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.example-item:hover {
  background: rgba(80, 80, 80, 0.7);
}

.example-item strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #fff;
}

.example-item pre {
  margin: 0;
  color: #aaa;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(116, 116, 116, 0.3);
}

.json-field {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
}

.json-editor {
  width: 100%;
  min-height: 120px;
  padding: 0.75rem;
  background: rgba(60, 60, 60, 0.8);
  border: 1px solid rgba(116, 116, 116, 0.5);
  border-radius: 4px;
  color: #fff;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  resize: vertical;
  transition: border-color 0.2s ease;
}

.json-editor:focus {
  outline: none;
  border-color: rgba(0, 145, 255, 0.8);
}

.json-editor::placeholder {
  color: #888;
}

.field-hint {
  display: block;
  margin-top: 0.25rem;
  color: #aaa;
  font-size: 0.75rem;
}

.error-message {
  margin-top: 0.25rem;
  color: #ff4444;
  font-size: 0.75rem;
}
</style>

