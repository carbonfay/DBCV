<template>
  <div class="credentials-container">
    <p class="credentials-info">Credentials (учетные данные) - это безопасные токены и ключи для подключения к внешним сервисам. Данные хранятся в зашифрованном виде и безопасны для ввода.</p>
    <BaseButton 
      @click="showCreateForm = !showCreateForm"
      size="small"
      styleType="secondary"
      class="add-button"
    >
      {{ showCreateForm ? 'Отменить' : 'Добавить' }}
    </BaseButton>

    <!-- Форма создания нового credential -->
    <div v-if="showCreateForm" class="create-form">
      <div class="form-row">
        <BaseInput
          v-model="formData.name"
          label="Название *"
          labelColor="#FFFFFF"
          class="dark"
        />
      </div>
      <div class="form-row">
        <BaseSelect
          v-model="formData.provider"
          label="Провайдер *"
          labelColor="#FFFFFF"
          :options="providerOptions"
          class="dark"
        />
      </div>
      <div class="form-row">
        <BaseSelect
          v-model="formData.strategy"
          label="Стратегия *"
          labelColor="#FFFFFF"
          :options="strategyOptions"
          class="dark"
        />
      </div>
      <div class="form-row">
        <label class="scopes-label">Scopes (области доступа) *</label>
        <div class="scopes-container">
          <div 
            v-for="(scope, index) in formData.scopes" 
            :key="index"
            class="scope-item"
          >
            <BaseInput
              v-model="formData.scopes[index]"
              :placeholder="`Scope ${index + 1}`"
              class="dark"
            />
            <BaseButton 
              @click.stop="removeScope(index)"
              size="small"
              styleType="danger"
            >
              ×
            </BaseButton>
          </div>
          <BaseButton 
            @click.stop="addScope"
            size="small"
            styleType="secondary"
          >
            + Добавить
          </BaseButton>
        </div>
      </div>
      <div class="form-row">
        <BaseCodeEditor
          v-model="formData.payload"
          label="Payload (JSON) *"
          language="json"
          :isCollapsed="false"
          :isResizable="false"
          :defaultHeight="150"
        />
        <div v-if="payloadError" class="payload-error">
          {{ payloadError }}
        </div>
        <div v-else-if="formData.provider && formData.strategy" class="payload-hint">
          Пример для {{ getProviderLabel() }} / {{ getStrategyLabel() }}:
          <code>{{ getPayloadExampleText() }}</code>
        </div>
      </div>
      <div class="form-row create-button">
        <BaseButton 
          @click="createCredential"
          size="small"
          styleType="secondary"
          :disabled="v$.$invalid"
        >
          Создать
        </BaseButton>
      </div>
    </div>
    
    <!-- Список существующих credentials -->
    <div v-if="credentials.length > 0" class="credentials-list">
      <div 
        v-for="credential in credentials" 
        :key="credential.id"
        class="credential-item"
        :class="{ 'is-default': credential.is_default }"
      >
        <div class="credential-info">
          <h3>{{ credential.name }}</h3>
          <p><strong>Provider:</strong> {{ credential.provider }}</p>
          <p><strong>Strategy:</strong> {{ credential.strategy }}</p>
          <p v-if="credential.scopes && credential.scopes.length > 0" class="scopes-display">
            <strong>Scopes: </strong> 
            <span 
              class="scopes-text" 
              :title="credential.scopes.join(', ')"
            >
              {{ credential.scopes.join(', ') }}
            </span>
          </p>
          <span v-if="credential.is_default" class="default-badge">Default</span>
        </div>
        <div class="credential-actions">
          <BaseButton 
            v-if="!credential.is_default" 
            @click="makeDefault(credential.id)"
            size="small"
            styleType="secondary"
          >
            Сделать default
          </BaseButton>
          <BaseButton 
            @click="deleteCredential(credential.id)" 
            size="small"
            styleType="danger"
          >
            x
          </BaseButton>
        </div>
      </div>
    </div>

    <div v-else class="no-credentials">
      Учетные данные не найдены
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue';
import { useCredentialsStore } from '@/stores';
import credentialsApi from '@/api/services/credentialsApi';
import type { Credential } from '@/types/store_types';
import { useVuelidate } from '@vuelidate/core';
import { credentialRules } from '@/plugins/vuelidate';
import notyf from '@/plugins/notyf';

interface Props {
  botId: string;
}

const props = defineProps<Props>();

const credentialsStore = useCredentialsStore();

const showCreateForm = ref(false);

const formData = reactive({
  name: '',
  provider: '',
  strategy: '',
  scopes: [''],
  is_default: false,
  payload: '{}',
});

const v$ = useVuelidate(credentialRules, formData);

// Валидация payload
const payloadError = ref<string>('');

// Computed для подсказок
const getProviderLabel = () => {
  const provider = providerOptions.value.find(p => p.value === formData.provider);
  return provider?.label || formData.provider || '';
};

const getStrategyLabel = () => {
  const strategy = strategyOptions.value.find(s => s.value === formData.strategy);
  return strategy?.label || formData.strategy || '';
};

const getPayloadExampleText = () => {
  if (!formData.provider || !formData.strategy) return '';
  const selectedProvider = providerOptions.value.find(p => p.value === formData.provider);
  if (selectedProvider?.payload_examples?.[formData.strategy]) {
    return JSON.stringify(selectedProvider.payload_examples[formData.strategy], null, 2);
  }
  return '';
};

// Валидация JSON при изменении payload
watch(() => formData.payload, (newPayload) => {
  payloadError.value = '';
  if (!newPayload || newPayload.trim() === '') {
    payloadError.value = 'Payload не может быть пустым';
    return;
  }
  try {
    const parsed = JSON.parse(newPayload);
    if (typeof parsed !== 'object' || Array.isArray(parsed)) {
      payloadError.value = 'Payload должен быть JSON объектом (не массивом)';
    }
  } catch (e) {
    payloadError.value = `Ошибка JSON: ${e instanceof Error ? e.message : 'Невалидный JSON'}`;
  }
}, { immediate: true });

// Опции для селектов (загружаются из API)
const providerOptions = ref<Array<{ value: string; label: string; description?: string; payload_examples?: any }>>([]);
const allStrategies = ref<Array<{ value: string; label: string; description?: string }>>([]);
const strategyOptions = computed(() => {
  if (!formData.provider) {
    return allStrategies.value;
  }
  
  // Находим выбранный провайдер и фильтруем стратегии
  const selectedProvider = providerOptions.value.find(p => p.value === formData.provider);
  if (!selectedProvider || !('supported_strategies' in selectedProvider)) {
    return allStrategies.value;
  }
  
  const supported = (selectedProvider as any).supported_strategies || [];
  return allStrategies.value.filter(s => supported.includes(s.value));
});

// Computed
const credentials = computed(() => credentialsStore.credentials || []);

const loadProviders = async () => {
  try {
    const response = await credentialsApi.getProviders();
    if (response?.data?.providers) {
      providerOptions.value = response.data.providers.map((p: any) => ({
        value: p.value,
        label: `${p.label}${p.description ? ` - ${p.description}` : ''}`,
        description: p.description,
        supported_strategies: p.supported_strategies,
        payload_examples: p.payload_examples || null,
      }));
    }
  } catch (error) {
    console.error('Error loading providers:', error);
  }
};

const loadStrategies = async (provider?: string) => {
  try {
    const response = await credentialsApi.getStrategies(provider);
    if (response?.data?.strategies) {
      allStrategies.value = response.data.strategies.map((s: any) => ({
        value: s.value,
        label: `${s.label}${s.description ? ` - ${s.description}` : ''}`,
        description: s.description,
      }));
    }
  } catch (error) {
    console.error('Error loading strategies:', error);
  }
};

const loadCredentials = async () => {
  const response = await credentialsStore.readCredentials(props.botId);
  console.log('response', response);
};

// Следим за изменением провайдера и обновляем стратегии
watch(() => formData.provider, async (newProvider) => {
  if (newProvider) {
    await loadStrategies(newProvider);
    // Сбрасываем стратегию, если она не поддерживается новым провайдером
    if (formData.strategy && !strategyOptions.value.find(s => s.value === formData.strategy)) {
      formData.strategy = '';
    }
    // Обновляем payload примером, если есть
    updatePayloadExample();
  } else {
    await loadStrategies();
  }
});

// Следим за изменением стратегии и обновляем payload примером
watch(() => formData.strategy, () => {
  updatePayloadExample();
});

// Функция для обновления payload примером
const updatePayloadExample = () => {
  if (!formData.provider || !formData.strategy) {
    return;
  }
  
  // Подставляем пример только если payload пустой или равен '{}'
  const currentPayload = formData.payload.trim();
  if (currentPayload !== '' && currentPayload !== '{}') {
    return;
  }
  
  const selectedProvider = providerOptions.value.find(p => p.value === formData.provider);
  if (selectedProvider?.payload_examples?.[formData.strategy]) {
    const example = selectedProvider.payload_examples[formData.strategy];
    formData.payload = JSON.stringify(example, null, 2);
  }
};

const addScope = () => {
  formData.scopes.push('');
};

const removeScope = (index: number) => {
  if (formData.scopes.length > 1) {
    formData.scopes.splice(index, 1);
  }
};

const createCredential = async () => {
  if (payloadError.value) {
    return;
  }
  
  try {
    let payload = {};
    try {
      payload = JSON.parse(formData.payload);
      if (typeof payload !== 'object' || Array.isArray(payload)) {
        payloadError.value = 'Payload должен быть JSON объектом';
        return;
      }
    } catch (e) {
      payloadError.value = `Ошибка JSON: ${e instanceof Error ? e.message : 'Невалидный JSON'}`;
      return;
    }

    // Подготавливаем данные для отправки
    const filteredScopes = (formData.scopes || []).filter(scope => scope && scope.trim() !== '');
    
    const credentialData = {
      name: formData.name,
      provider: formData.provider, // Должна быть строка, например "telegram"
      strategy: formData.strategy, // Должна быть строка, например "api_key"
      bot_id: props.botId,
      payload,
      scopes: filteredScopes.length > 0 ? filteredScopes : null, // null если пусто
      is_default: formData.is_default,
    };

    const result = await credentialsStore.createCredential(props.botId, credentialData);
    
    if (!result) {
      // Ошибка создания - возможно, проблема с API или валидацией
      console.error('Failed to create credential - response was null');
      notyf.error('Ошибка создания credential. Проверьте данные и попробуйте снова.');
      return;
    }
    
    // Сброс формы и скрытие
    Object.assign(formData, {
      name: '',
      provider: '',
      strategy: '',
      scopes: [''],
      is_default: false,
      payload: '{}',
    });
    v$.value.$reset();
    showCreateForm.value = false;
    
    // Перезагружаем список credentials
    await loadCredentials();
    notyf.success('Credential успешно создан!');
  } catch (error) {
    console.error('Error creating credential:', error);
    notyf.error('Ошибка при создании credential. Попробуйте снова.');
  }
};

const makeDefault = async (credId: string) => {
  await credentialsStore.makeDefaultCredential(props.botId, credId);
};

const deleteCredential = async (credId: string) => {
  if (confirm('Are you sure you want to delete this credential?')) {
    await credentialsStore.deleteCredential(props.botId, credId);
  }
};

onMounted(async () => {
  await loadProviders();
  await loadStrategies();
  await loadCredentials();
});
</script>

<style scoped>
.credentials-info {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.add-button {
  margin: 10px 0;
}

.credentials-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.credential-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border: 1px solid rgba(116, 116, 116, 1);
  border-radius: 6px;
  background: #2a2a2a;
  font-size: 12px;
  gap: 10px;
}

.credential-item.is-default {
  border-color: #007bff;
  background: #1a3a5c;
}

.credential-info h3 {
  margin: 0 0 5px;
}

.credential-info p {
  color: #ccc;
  font-size: 11px;
}

.scopes-display {
  word-break: break-all;
  overflow-wrap: break-word;
  max-width: 100%;
}

.scopes-text {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: top;
}

.default-badge {
  display: inline-block;
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-top: 10px;
}

.credential-actions {
  display: flex;
  gap: 10px;
}

.no-credentials {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 12px;
}

.create-form {
  background: #2a2a2a;
  padding: 15px 10px;
  border-radius: 8px;
  border: 1px solid rgba(116, 116, 116, 1);
  margin-bottom: 10px;
}

.form-row {
  margin-bottom: 12px;
}

.form-row.create-button {
  display: flex;
  justify-content: flex-end;
}

.scopes-label {
  display: block;
  font-size: 14px;
  margin-bottom: 3px;
}

.scopes-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scope-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.scope-item .base-input {
  flex: 1;
}

.input-wrapper.dark,
.custom-select-wrapper.dark {
  gap: 3px;
}

.payload-error {
  color: #ff4444;
  font-size: 11px;
  margin-top: 5px;
  padding: 5px;
  background: rgba(255, 68, 68, 0.1);
  border-radius: 4px;
}

.payload-hint {
  color: rgba(255, 255, 255, 0.6);
  font-size: 11px;
  margin-top: 5px;
  padding: 5px;
}

.payload-hint code {
  display: block;
  margin-top: 3px;
  padding: 5px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>