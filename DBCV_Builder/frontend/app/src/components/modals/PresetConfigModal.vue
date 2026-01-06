<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal" @click.stop>
      <div class="modal-head">
        <div class="modal-name">{{ preset?.name || 'Настройка preset' }}</div>
        <button class="modal-close" @click="handleClose">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="preset?.description" class="preset-description">
          {{ preset.description }}
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div
            v-for="field in formFields"
            :key="field.key"
            class="form-field"
          >
            <!-- Текстовое поле -->
            <BaseInput
              v-if="field.type === 'string' && !field.enum && field.format !== 'uuid'"
              v-model="formData[field.key]"
              :label="field.title + (field.required ? ' *' : '')"
              :placeholder="field.description || field.title"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
            <!-- UUID поле (для step_id) -->
            <div v-else-if="field.format === 'uuid'">
              <BaseInput
                v-model="formData[field.key]"
                :label="field.title + (field.required ? ' *' : '')"
                :placeholder="field.description || 'UUID шага'"
                labelColor="#FFFFFF"
                :error="errors[field.key]"
              />
              <small class="field-hint">Введите UUID существующего шага</small>
            </div>
            
            <!-- Select для enum -->
            <BaseSelect
              v-else-if="field.type === 'string' && field.enum"
              v-model="formData[field.key]"
              :options="field.enum.map((v: any) => ({ value: v, label: v }))"
              :label="field.title + (field.required ? ' *' : '')"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
            <!-- Number поле -->
            <BaseInput
              v-else-if="field.type === 'number' || field.type === 'integer'"
              v-model.number="formData[field.key]"
              type="number"
              :label="field.title + (field.required ? ' *' : '')"
              :placeholder="field.description || field.title"
              labelColor="#FFFFFF"
              :error="errors[field.key]"
            />
            
            <!-- Boolean поле -->
            <BaseCheckbox
              v-else-if="field.type === 'boolean'"
              v-model="formData[field.key]"
              :label="field.title + (field.required ? ' *' : '')"
            />
            
            <!-- Object поле (для condition) - JSON редактор -->
            <div v-else-if="field.type === 'object'">
              <label class="field-label">
                {{ field.title + (field.required ? ' *' : '') }}
              </label>
              <textarea
                v-model="formDataJson[field.key]"
                class="json-editor"
                :placeholder="field.description || 'JSON объект'"
                @input="handleJsonInput(field.key)"
              />
              <small class="field-hint">{{ field.description || 'Введите JSON объект' }}</small>
              <div v-if="errors[field.key]" class="error-message">{{ errors[field.key] }}</div>
            </div>
          </div>
          
          <div v-if="preset?.examples && preset.examples.length > 0" class="examples-section">
            <h4>Примеры:</h4>
            <div
              v-for="(example, idx) in preset.examples"
              :key="idx"
              class="example-item"
              @click="loadExample(example.config)"
            >
              <strong>{{ example.description || `Пример ${idx + 1}` }}</strong>
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
import presetsApi from '@/api/services/presetsApi';
import notyf from '@/plugins/notyf';

const props = defineProps<{
  preset: any;
  botId: string;
  posX?: number;
  posY?: number;
}>();

const emit = defineEmits(['close', 'created']);

const formData = ref<Record<string, any>>({});
const formDataJson = ref<Record<string, string>>({});
const errors = ref<Record<string, string>>({});
const isSubmitting = ref(false);

const formFields = computed(() => {
  if (!props.preset?.config_schema?.properties) return [];
  
  const schema = props.preset.config_schema;
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
  () => props.preset,
  (preset) => {
    if (preset?.config_schema?.properties) {
      const schema = preset.config_schema;
      const initialData: Record<string, any> = {};
      const initialJson: Record<string, string> = {};
      
      Object.entries(schema.properties).forEach(([key, prop]: [string, any]) => {
        // Инициализируем значение (default или пустое)
        if (prop.default !== undefined) {
          initialData[key] = prop.default;
        } else if (prop.type === 'object') {
          // Для object типов инициализируем пустым объектом
          initialData[key] = {};
        }
        
        // Для object типов создаем JSON строку
        if (prop.type === 'object') {
          const value = initialData[key] || {};
          initialJson[key] = JSON.stringify(value, null, 2);
        }
      });
      
      formData.value = initialData;
      formDataJson.value = initialJson;
    }
  },
  { immediate: true }
);

const handleJsonInput = (key: string) => {
  const jsonString = formDataJson.value[key] || '{}';
  try {
    const parsed = JSON.parse(jsonString);
    formData.value[key] = parsed;
    // Убираем ошибку если была
    if (errors.value[key]) {
      delete errors.value[key];
    }
  } catch (e) {
    // Сохраняем ошибку, но не блокируем ввод
    // Проверяем, что это не просто пустая строка
    if (jsonString.trim() !== '') {
      errors.value[key] = 'Некорректный JSON';
    } else {
      // Если пустая строка, очищаем ошибку и устанавливаем пустой объект
      delete errors.value[key];
      formData.value[key] = {};
    }
  }
};

const validateForm = () => {
  errors.value = {};
  let isValid = true;
  
  if (!props.preset?.config_schema?.required) return isValid;
  
  props.preset.config_schema.required.forEach((key: string) => {
    const prop = props.preset.config_schema.properties[key];
    const value = formData.value[key];
    
    // Для object типов проверяем, что JSON валидный
    if (prop?.type === 'object') {
      const jsonString = formDataJson.value[key] || '{}';
      try {
        const parsed = JSON.parse(jsonString);
        // Проверяем, что это не пустой объект (если требуется)
        if (Object.keys(parsed).length === 0 && value === undefined) {
          errors.value[key] = 'Это поле обязательно';
          isValid = false;
        } else {
          // Синхронизируем formData с распарсенным значением
          formData.value[key] = parsed;
        }
      } catch (e) {
        errors.value[key] = 'Некорректный JSON';
        isValid = false;
      }
    } else {
      // Для остальных типов
      if (value === undefined || value === null || value === '') {
        errors.value[key] = 'Это поле обязательно';
        isValid = false;
      }
      
      // Дополнительная валидация для UUID
      if (prop?.format === 'uuid') {
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (value && !uuidRegex.test(value)) {
          errors.value[key] = 'Некорректный формат UUID';
          isValid = false;
        }
      }
    }
  });
  
  return isValid;
};

const loadExample = (exampleConfig: Record<string, any>) => {
  // Обновляем formData
  formData.value = { ...formData.value, ...exampleConfig };
  
  // Обновляем JSON поля для всех object типов
  if (props.preset?.config_schema?.properties) {
    Object.entries(props.preset.config_schema.properties).forEach(([key, prop]: [string, any]) => {
      if (prop.type === 'object') {
        const value = exampleConfig[key] !== undefined ? exampleConfig[key] : formData.value[key] || {};
        formDataJson.value[key] = JSON.stringify(value, null, 2);
        // Также обновляем formData для этого поля
        formData.value[key] = value;
      }
    });
  }
};

const handleSubmit = async () => {
  // Перед отправкой убеждаемся, что все JSON поля синхронизированы
  Object.keys(formDataJson.value).forEach((key) => {
    try {
      const parsed = JSON.parse(formDataJson.value[key] || '{}');
      formData.value[key] = parsed;
    } catch (e) {
      // Игнорируем ошибки парсинга, валидация уже проверила
    }
  });
  
  if (!validateForm()) {
    notyf.error('Пожалуйста, заполните все обязательные поля');
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // Создаем чистый объект config без undefined значений
    const config: Record<string, any> = {};
    Object.keys(formData.value).forEach((key) => {
      if (formData.value[key] !== undefined) {
        config[key] = formData.value[key];
      }
    });
    
    const response = await presetsApi.createStepFromPreset({
      preset_id: props.preset.id,
      bot_id: props.botId,
      config: config,
      pos_x: props.posX,
      pos_y: props.posY,
    });
    
    if (!response?.data) {
      throw new Error('Не удалось создать шаг');
    }
    
    notyf.success('Шаг с preset успешно создан');
    emit('created', response.data);
    handleClose();
  } catch (error: any) {
    console.error('Error creating preset step:', error);
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

.preset-description {
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

.field-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
}

.json-editor {
  width: 100%;
  min-height: 150px;
  padding: 0.75rem;
  background: rgba(40, 40, 40, 0.8);
  border: 1px solid rgba(116, 116, 116, 0.5);
  border-radius: 4px;
  color: #fff;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  resize: vertical;
}

.json-editor:focus {
  outline: none;
  border-color: rgba(0, 145, 255, 0.8);
}

.field-hint {
  display: block;
  margin-top: 0.25rem;
  color: #888;
  font-size: 0.75rem;
}

.error-message {
  margin-top: 0.25rem;
  color: #ff4444;
  font-size: 0.75rem;
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
</style>

