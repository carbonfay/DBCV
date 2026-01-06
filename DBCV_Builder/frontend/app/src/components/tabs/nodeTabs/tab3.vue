<template>
  <div class="dynamic-blocks">
    <div v-for="(block, index) in blocks" :key="index" class="block">
      <h3>Группа связей № {{ index + 1 }}</h3>
      <div class="content">
        <BaseSelect
          v-model="block.selectedOption"
          :options="options"
          :label="'Тип поиска'"
          class="first-select"
          @input="isSomethingChangedArr[index] = true"
        />
        <div v-if="block.selectedOption === 'code'">
          <BaseCodeEditor
            label="Код"
            :labelColor="'rgb(30, 30, 30)'"
            language="python"
            :is-collapsed="false"
            :is-resizable="false"
            :auto-height="true"
            :default-height="200"
            v-model="block.textareaValue"
            @input="isSomethingChangedArr[index] = true"
            class="code-editor"
            light-theme
            small
          />
        </div>
        <div class="response-block" v-if="block.selectedOption === 'response'">
          <BaseSelectSearch
            v-model="block.inputValue"
            :options="requestsOptions"
            label="Запрос"
            :labelColor="'rgb(30, 30, 30)'"
            @input="isSomethingChangedArr[index] = true"
          />
          <button
            class="request-action-btn edit-btn"
            :disabled="!block.inputValue"
            @click="handleRequestActionEdit(block)"
          >
            <EditIcon class="icon" />
          </button>
          <button
            class="request-action-btn execute-btn"
            :disabled="!block.inputValue || isExecuting"
            @click="handleRequestActionExecute(block)"
          >
            {{ isExecuting ? '...' : 'Execute' }}
          </button>
          <button class="request-action-btn create-btn" @click="handleRequestActionCreate(block)">
            +
          </button>
        </div>
        <div class="integration-block" v-if="block.selectedOption === 'integration'">
          <BaseSelectSearch
            v-model="block.integrationId"
            :options="integrationsOptions"
            label="Интеграция"
            :labelColor="'rgb(30, 30, 30)'"
            @input="block.integrationId && handleIntegrationSelect(index, block.integrationId)"
          />
          <div v-if="block.integrationConfig && block.integrationId && integrationMetadataMap[block.integrationId]" class="integration-config">
            <h4>{{ integrationMetadataMap[block.integrationId]?.name }}</h4>
            <div
              v-for="field in getIntegrationFormFields(index)"
              :key="field.key"
              class="config-field"
            >
              <BaseInput
                v-if="field.type === 'string' && !field.enum"
                v-model="block.integrationConfig[field.key]"
                :label="field.title + (field.required ? ' *' : '')"
                :placeholder="field.description || field.title"
                :labelColor="'rgb(30, 30, 30)'"
                @input="isSomethingChangedArr[index] = true"
              />
              <BaseSelect
                v-else-if="field.type === 'string' && field.enum"
                v-model="block.integrationConfig[field.key]"
                :options="field.enum.map((v: any) => ({ value: v, label: v }))"
                :label="field.title + (field.required ? ' *' : '')"
                :labelColor="'rgb(30, 30, 30)'"
                @input="isSomethingChangedArr[index] = true"
              />
              <BaseInput
                v-else-if="field.type === 'number' || field.type === 'integer'"
                v-model.number="block.integrationConfig[field.key]"
                type="number"
                :label="field.title + (field.required ? ' *' : '')"
                :placeholder="field.description || field.title"
                :labelColor="'rgb(30, 30, 30)'"
                @input="isSomethingChangedArr[index] = true"
              />
              <BaseCheckbox
                v-else-if="field.type === 'boolean'"
                v-model="block.integrationConfig[field.key]"
                :label="field.title + (field.required ? ' *' : '')"
                @input="isSomethingChangedArr[index] = true"
              />
              
              <!-- Array и Object поля - JSON редактор -->
              <div v-else-if="field.type === 'array' || field.type === 'object'" class="json-field">
                <label class="field-label">
                  {{ field.title + (field.required ? ' *' : '') }}
                </label>
                <textarea
                  :value="getJsonFieldValue(block.integrationConfig, field.key)"
                  class="json-editor"
                  :placeholder="field.description || (field.type === 'array' ? 'JSON массив, например: [1, 2, 3]' : 'JSON объект, например: {&quot;key&quot;: &quot;value&quot;}')"
                  @input="handleJsonFieldInput(index, field.key, $event)"
                />
                <small class="field-hint">{{ field.description || (field.type === 'array' ? 'Введите JSON массив' : 'Введите JSON объект') }}</small>
              </div>
            </div>
          </div>
        </div>
        <!-- Раздел "Сохранить как" -->
        <div class="save-as-section">
          <span class="label">Сохранить результат</span>
          <div class="columns">
            <div class="column">
              <div v-for="(row, rowIndex) in block.saveAsRows" :key="rowIndex" class="row">
                <BaseInput
                  v-model="row.left"
                  :label="''"
                  :placeholder="'Ключ'"
                  :labelColor="'rgb(30, 30, 30)'"
                  @input="isSomethingChangedArr[index] = true"
                />
              </div>
            </div>
            <div class="column">
              <div v-for="(row, rowIndex) in block.saveAsRows" :key="rowIndex" class="row">
                <BaseInput
                  v-model="row.right"
                  :label="''"
                  :placeholder="'Значение'"
                  :labelColor="'rgb(30, 30, 30)'"
                  @input="isSomethingChangedArr[index] = true"
                />
              </div>
            </div>
          </div>
          <button class="add-button" @click="addSaveAsRow(index)">Добавить переменную</button>
        </div>
        <!-- Раздел "Связи" -->
        <div class="connections-section">
          <div
            v-for="(connection, connectionIndex) in block.connections"
            :key="connectionIndex"
            class="connection"
          >
            <h3>Связь № {{ connectionIndex + 1 }}</h3>
            <div class="connection-content">
              <BaseSelect
                v-model="connection.type"
                :options="connectionOptions"
                :label="'Следующий шаг'"
                class="first-select"
                @input="isSomethingChangedArr[index] = true"
              />
              <BaseCodeEditor
                label="Правила"
                :labelColor="'rgb(30, 30, 30)'"
                language="json"
                :is-collapsed="false"
                :is-resizable="false"
                :default-height="100"
                v-model="connection.rules"
                @input="isSomethingChangedArr[index] = true"
                class="code-editor"
                light-theme
                small
              />
            </div>
            <div class="connection-btns">
              <div v-if="block.connections.length > 1" class="move-btns">
                <button
                  @click="moveConnectionUp(index, connectionIndex)"
                  :disabled="connectionIndex === 0"
                >
                  <TopArrowIcon />
                </button>
                <button
                  @click="moveConnectionDown(index, connectionIndex)"
                  :disabled="connectionIndex === block.connections.length - 1"
                >
                  <BottomArrowIcon />
                </button>
              </div>
              <button @click.stop="removeConnection(index, connectionIndex)">
                <TrashIcon class="icon icon-trash" />
              </button>
            </div>
          </div>
          <BaseButton styleType="primary" size="small" @click="addConnection(index)">
            Добавить связь
          </BaseButton>
        </div>
      </div>
      <div class="btns">
        <div v-if="blocks.length > 1" class="move-btns">
          <button @click="moveUp(index)" :disabled="index === 0">
            <TopArrowIcon />
          </button>
          <button @click="moveDown(index)" :disabled="index === blocks.length - 1">
            <BottomArrowIcon />
          </button>
        </div>
        <button @click="removeConnectionGroup(index)">
          <TrashIcon class="icon icon-trash" />
        </button>
        <BaseButton styleType="primary" size="small" @click="saveData(index)">Сохранить</BaseButton>
      </div>
    </div>
    <BaseButton styleType="secondary" size="small" @click="addConnectionGroup">
      Добавить группу связей
    </BaseButton>
    <requestModal
      v-if="isRequestModalOpen"
      :isEditMode="isEditMode"
      :formData="currentFormData"
      :currentRequestId="currentRequestId"
      @close="closeRequestModal"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue';
import { BottomArrowIcon, EditIcon, TopArrowIcon, TrashIcon } from '@/components/icons'; // импорт иконок
import { useConnectionGroupsStore, useRequestsStore } from '@/stores'; // импорт stores
import notyf from '@/plugins/notyf';
import requestModal from '@/components/modals/requestModal.vue';
import integrationsApi from '@/api/services/integrationsApi';

interface Block {
  id?: string;
  selectedOption: string;
  textareaValue: string;
  inputValue: string;
  integrationId?: string | null;
  integrationConfig?: Record<string, any> | null;
  saveAsRows: Array<{ left: string; right: string }>;
  connections: Array<{ type: string; rules: string }>;
}

const props = defineProps<{
  node: any;
}>();

const isRequestModalOpen = ref(false);
const isEditMode = ref(false);
const currentRequestId = ref<string | null>(null);

const currentFormData = ref({
  name: '',
  request_url: '',
  method: 'GET',
  params: null,
  data: null,
  content: null,
  headers: null,
  url_params: null,
  attachments: null,
  json_field: null,
  proxies: null,
});

const connectionGroupsStore = useConnectionGroupsStore();
const requestsStore = useRequestsStore();

const blocks = ref<Block[]>([]);
const nodes = inject<any>('nodes');
const edges = inject<any>('edges');
const isExecuting = ref(false);

const emit = defineEmits<{
  (e: 'graphUpdate-node', node: any): void;
}>();

const isSomethingChangedArr = ref(
  Array.from({ length: props.node.data.connection_groups?.length ?? 0 }).fill(false)
);

const isSomethingChanged = computed(() => {
  return isSomethingChangedArr.value.indexOf(true) !== -1;
});

// Код для Connection-Group
const addConnectionGroup = async () => {
  const newGroupData = {
    search_type: 'message',
    priority: blocks.value.length,
    step_id: props.node.id,
    code: null,
    request_id: null,
    integration_id: null,
    integration_config: null,
    variables: null,
    connections: [],
  };

  const response = await connectionGroupsStore.createConnectionGroup(newGroupData);

  blocks.value.push({
    id: response.id,
    selectedOption: 'message',
    textareaValue: '',
    inputValue: '',
    integrationId: null,
    integrationConfig: null,
    saveAsRows: [{ left: '', right: '' }],
    connections: [],
  });

  emit('graphUpdate-node', { id: props.node.id, ...props.node });
  isSomethingChangedArr.value.push(false);
};

const removeConnectionGroup = async (index: number) => {
  const blockToRemove = blocks.value[index];

  if (!blockToRemove.id) {
    console.warn('Невозможно удалить группу без ID');
    return;
  }

  await connectionGroupsStore.deleteConnectionGroup(blockToRemove.id);
  blocks.value.splice(index, 1);

  emit('graphUpdate-node', { id: props.node.id, ...props.node });
  isSomethingChangedArr.value = isSomethingChangedArr.value.splice(index, 1);
};

const moveUp = (index: number) => {
  if (index > 0) {
    isSomethingChangedArr.value[index] = true;
    isSomethingChangedArr.value[index - 1] = true;
    [blocks.value[index - 1], blocks.value[index]] = [blocks.value[index], blocks.value[index - 1]];
  }
};

const moveDown = (index: number) => {
  if (index < blocks.value.length - 1) {
    isSomethingChangedArr.value[index] = true;
    isSomethingChangedArr.value[index + 1] = true;
    [blocks.value[index + 1], blocks.value[index]] = [blocks.value[index], blocks.value[index + 1]];
  }
};

// Код для Connection
const addConnection = (blockIndex: number) => {
  const defaultOption = connectionOptions.value[0]?.value || '';
  blocks.value[blockIndex].connections.push({
    type: defaultOption,
    rules: '',
  });
  isSomethingChangedArr.value[blockIndex] = true;
};

const removeConnection = (blockIndex: number, connectionIndex: number) => {
  blocks.value[blockIndex].connections.splice(connectionIndex, 1);
  isSomethingChangedArr.value[blockIndex] = true;
};

const moveConnectionUp = (blockIndex: number, connectionIndex: number) => {
  if (connectionIndex > 0) {
    isSomethingChangedArr.value[blockIndex] = true;
    const connections = blocks.value[blockIndex].connections;
    [connections[connectionIndex - 1], connections[connectionIndex]] = [
      connections[connectionIndex],
      connections[connectionIndex - 1],
    ];
  }
};

const moveConnectionDown = (blockIndex: number, connectionIndex: number) => {
  if (connectionIndex < blocks.value[blockIndex].connections.length - 1) {
    isSomethingChangedArr.value[blockIndex] = true;
    const connections = blocks.value[blockIndex].connections;
    [connections[connectionIndex + 1], connections[connectionIndex]] = [
      connections[connectionIndex],
      connections[connectionIndex + 1],
    ];
  }
};

// Метод для добавления строки в раздел "Сохранить как"
const addSaveAsRow = (blockIndex: number) => {
  isSomethingChangedArr.value[blockIndex] = true;
  blocks.value[blockIndex].saveAsRows.push({ left: '', right: '' });
};

// Наполнение селектов
const options = [
  { value: 'code', label: 'Код' },
  { value: 'response', label: 'Request' },
  { value: 'message', label: 'Message' },
  { value: 'integration', label: 'Integration' },
];

const connectionOptions = computed(() => {
  if (!nodes || !nodes.value) return [];
  return (nodes.value as any[])
    .filter((node: any) => node.id !== props.node.id)
    .map((node: any) => ({
      value: node.id,
      label: node.data.name || `Узел ${node.id}`,
    }));
});

const requestsOptions = computed(() => {
  return requestsStore.requests.map((request) => ({
    value: request.id,
    label: request.name || `Реквест ${request.id}`,
  }));
});

// Интеграции
const integrations = ref([] as any[]);
const integrationMetadataMap = ref({} as Record<string, any>);

const integrationsOptions = computed(() => {
  return integrations.value.map((integration) => ({
    value: integration.id,
    label: integration.name,
  }));
});

const getIntegrationFormFields = (blockIndex: number) => {
  const block = blocks.value[blockIndex];
  if (!block.integrationId) return [];
  const metadata = integrationMetadataMap.value[block.integrationId];
  
  if (!metadata?.config_schema?.properties) return [];
  
  const schema = metadata.config_schema;
  const required = schema.required || [];
  
  return Object.entries(schema.properties).map(([key, prop]: [string, any]) => ({
    key,
    title: (prop as any).title || key,
    description: (prop as any).description,
    type: (prop as any).type,
    enum: (prop as any).enum,
    format: (prop as any).format,
    required: required.includes(key),
    default: (prop as any).default,
  }));
};

const getJsonFieldValue = (config: Record<string, any> | null, key: string): string => {
  if (!config || !config[key]) {
    return '';
  }
  try {
    return JSON.stringify(config[key], null, 2);
  } catch {
    return String(config[key]);
  }
};

const handleJsonFieldInput = (blockIndex: number, key: string, event: Event) => {
  const textarea = event.target as HTMLTextAreaElement;
  const jsonString = textarea.value || '';
  
  if (!blocks.value[blockIndex].integrationConfig) {
    blocks.value[blockIndex].integrationConfig = {};
  }
  
  if (!jsonString.trim()) {
    delete blocks.value[blockIndex].integrationConfig![key];
    isSomethingChangedArr.value[blockIndex] = true;
    return;
  }
  
  try {
    const parsed = JSON.parse(jsonString);
    blocks.value[blockIndex].integrationConfig![key] = parsed;
    isSomethingChangedArr.value[blockIndex] = true;
  } catch (e) {
    // Оставляем как есть, пользователь может еще редактировать
    console.warn('Invalid JSON:', e);
  }
};

const handleIntegrationSelect = async (blockIndex: number, integrationId: string) => {
  if (!integrationId) {
    blocks.value[blockIndex].integrationConfig = null;
    delete integrationMetadataMap.value[integrationId];
    return;
  }
  
  try {
    const response = await integrationsApi.getMetadata(integrationId);
    if (response?.data) {
      integrationMetadataMap.value[integrationId] = response.data;
      
      // Инициализируем config с дефолтными значениями, если его еще нет
      if (!blocks.value[blockIndex].integrationConfig) {
        const config = {} as Record<string, any>;
        if (response.data.config_schema?.properties) {
          Object.entries(response.data.config_schema.properties).forEach(([key, prop]: [string, any]) => {
            if ((prop as any).default !== undefined) {
              config[key] = (prop as any).default;
            } else if ((prop as any).type === 'object') {
              config[key] = {};
            } else if ((prop as any).type === 'array') {
              config[key] = [];
            }
          });
        }
        blocks.value[blockIndex].integrationConfig = config;
      }
      
      blocks.value[blockIndex].integrationId = integrationId;
      isSomethingChangedArr.value[blockIndex] = true;
    }
  } catch (error) {
    console.error('Error loading integration metadata:', error);
    notyf.error('Ошибка загрузки метаданных интеграции');
  }
};

const loadIntegrations = async () => {
  try {
    const response = await integrationsApi.getCatalog();
    if (response?.data?.items) {
      integrations.value = response.data.items;
    }
  } catch (error) {
    console.error('Error loading integrations:', error);
  }
};

// При создании реквеста
const handleRequestActionCreate = (block?: Block) => {
  isEditMode.value = false;
  currentRequestId.value = null;
  currentFormData.value = {
    name: '',
    request_url: '',
    method: 'GET',
    params: null,
    data: null,
    content: null,
    headers: null,
    url_params: null,
    attachments: null,
    json_field: null,
    proxies: null,
  };
  isRequestModalOpen.value = true;
};

// При редактированиии реквеста
const handleRequestActionEdit = async (block: Block) => {
  if (!block.inputValue) return;

  isEditMode.value = true;
  currentRequestId.value = block.inputValue;

  const request = requestsStore.requests.find((req) => req.id === block.inputValue);
  if (request) {
    Object.assign(currentFormData.value, request);
  } else {
    console.error('Реквест с указанным ID не найден');
  }

  isRequestModalOpen.value = true;
};

// При выполнении реквеста
const handleRequestActionExecute = async (block: Block) => {
  if (!block.inputValue) return;

  isExecuting.value = true;

  try {
    // Получаем реквест для извлечения переменных
    const request = requestsStore.requests.find((req: any) => req.id === block.inputValue);
    const variables = (request as any)?.variables || { channel: {}, user: {}, bot: {}, session: {} };
    const dryRun = (request as any)?.dry_run || false;
    
    const response = await requestsStore.executeRequest(block.inputValue, variables, dryRun);
    if (response?.data) {
      const action = dryRun ? 'проверка подстановки' : 'выполнение запроса';
      notyf.success(`${action} выполнена успешно!`);
      console.log('Результат выполнения запроса:', response.data);
    } else {
      notyf.error('Не удалось выполнить запрос');
    }
  } catch (error) {
    notyf.error('Ошибка при выполнении запроса: ' + ((error as any)?.message || 'Неизвестная ошибка'));
    console.error('Ошибка выполнения запроса:', error);
  } finally {
    isExecuting.value = false;
  }
};

// Закрытие модального окна реквестов
const closeRequestModal = () => {
  isRequestModalOpen.value = false;
  const updatedRequest = requestsStore.requests.find((req) => req.id === currentRequestId.value);
  if (updatedRequest) {
    const block = blocks.value.find((b) => b.inputValue === currentRequestId.value);
    if (block) {
      block.inputValue = updatedRequest.id;
    }
  }
};

// Клик по кнопке "сохранить"
const saveData = async (blockIndex: number) => {
  const block = blocks.value[blockIndex];

  const variables = block.saveAsRows.reduce((acc: Record<string, string>, row: { left: string; right: string }) => {
    if (row.left && row.right) {
      acc[row.left] = row.right;
    }
    return acc;
  }, {});

  const connections = block.connections.map((connection: { type: string; rules: string }, index: number) => {
    // Преобразуем rules из JSON строки в объект для отправки на сервер
    let rulesValue: any = null;
    if (connection.rules && connection.rules.trim()) {
      try {
        rulesValue = JSON.parse(connection.rules);
      } catch (e) {
        // Если не валидный JSON, отправляем как есть (может быть пустая строка или null)
        rulesValue = connection.rules.trim() || null;
      }
    }
    return {
      next_step_id: connection.type,
      rules: rulesValue,
      priority: index,
      filters: null,
    };
  });

  const connectionGroupData = {
    id: block.id,
    search_type: block.selectedOption,
    priority: blockIndex,
    step_id: props.node.id,
    code: block.selectedOption === 'code' ? block.textareaValue : null,
    request_id: block.selectedOption === 'response' ? block.inputValue || null : null,
    integration_id: block.selectedOption === 'integration' ? block.integrationId || null : null,
    integration_config: block.selectedOption === 'integration' ? block.integrationConfig || null : null,
    variables: JSON.stringify(variables),
    connections: connections,
  };

  if (!connectionGroupData.id) return;
  await connectionGroupsStore.updateConnectionGroup(connectionGroupData.id, connectionGroupData);
  notyf.success('Сохранено!');
  emit('graphUpdate-node', { id: props.node.id, ...props.node });
  isSomethingChangedArr.value[blockIndex] = false;
};

// Показывать существующие Connection group
const initializeBlocks = () => {
  if (props.node.data?.connection_groups?.length ?? 0 > 0) {
    blocks.value = (props.node.data.connection_groups as any[]).map((group: any) => {
      const parsedVariables = group.variables ? JSON.parse(group.variables) : {};

      return {
        id: group.id,
        selectedOption: group.search_type,
        textareaValue: group.code || '',
        inputValue: group.request_id || '',
        integrationId: group.integration_id || null,
        integrationConfig: group.integration_config || null,
        saveAsRows: Object.entries(parsedVariables).map(([key, value]: [string, any]) => ({
          left: key,
          right: value,
        })),
        connections: (group.connections || []).map((connection: any) => {
          // Преобразуем rules из объекта в JSON строку, если это объект
          let rulesValue = '';
          if (connection.rules) {
            if (typeof connection.rules === 'object') {
              rulesValue = JSON.stringify(connection.rules, null, 2);
            } else if (typeof connection.rules === 'string') {
              // Если уже строка, проверяем что это валидный JSON
              try {
                JSON.parse(connection.rules);
                rulesValue = connection.rules;
              } catch {
                // Если не валидный JSON, пытаемся распарсить как объект
                rulesValue = JSON.stringify(connection.rules, null, 2);
              }
            }
          }
          return {
            type: connection.next_step_id,
            rules: rulesValue,
          };
        }),
      } as Block;
    });
  }
};

const save = async () => {
  for (let i = 0; i < blocks.value.length; i++) await saveData(i);
  emit('graphUpdate-node', { id: props.node.id, ...props.node });
};

defineExpose({
  isSomethingChanged,
  save,
});

onMounted(async () => {
  await requestsStore.readRequests();
  await loadIntegrations();
  initializeBlocks();
  
  // Загружаем метаданные для существующих интеграций
  for (let i = 0; i < blocks.value.length; i++) {
    const block = blocks.value[i];
    if (block.selectedOption === 'integration' && block.integrationId) {
      await handleIntegrationSelect(i, block.integrationId);
    }
  }
});
</script>

<style scoped>
.block,
.connection {
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border: 2px solid rgb(227, 227, 227);
  border-radius: 10px;
  padding: 10px 15px;
  margin-bottom: 13px;
}

.connections-section {
  margin: 20px 0 10px;
}

.connections-section .connection {
  border: 1px solid rgb(30, 30, 30);
}

h3 {
  color: rgb(0, 0, 0);
  font-size: 10px;
  font-weight: 900;
  line-height: 10px;
  text-transform: uppercase;
  margin: 0 0 10px;
}

p {
  color: rgb(0, 0, 0);
}

.first-select {
  margin-bottom: 10px;
}

.save-as-section {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
}

.save-as-section .columns {
  display: flex;
  gap: 10px;
}

.save-as-section .column {
  flex: 1;
}

.save-as-section .row {
  margin-bottom: 5px;
}

.save-as-section .label {
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  margin: 0;
}

.save-as-section button {
  align-self: flex-end;
}

.btns,
.connection-btns {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 10px;
}

.btns .move-btns,
.connection-btns .move-btns {
  display: flex;
  margin-right: auto;
}

.icon-trash {
  width: 16px;
  height: 16px;
  margin-right: 10px;
  stroke: black;
}

button {
  color: rgb(30, 30, 30);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.code-editor {
  gap: 2px;
}

.response-block {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

button.request-action-btn {
  border: 1px solid rgb(217, 217, 217);
  background-color: #fff;
  border-radius: 8px;
  padding: 8px;
  font-size: 14px;
  font-weight: 600;
  width: 100%;
  max-width: 34px;
  height: 34px;
}

button.request-action-btn.execute-btn {
  background-color: #4caf50;
  color: white;
  border-color: #4caf50;
}

button.request-action-btn.execute-btn:hover:not(:disabled) {
  background-color: #45a049;
}

button.request-action-btn.execute-btn:disabled {
  background-color: #ccc;
  border-color: #ccc;
  color: #666;
}

.add-button {
  padding: 8px 16px;
  border-radius: 4px;
}

.add-button:hover {
  background-color: #e0e0e0;
}

.integration-block {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(240, 240, 240, 0.5);
  border-radius: 4px;
}

.integration-config {
  margin-top: 1rem;
}

.integration-config h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: rgb(30, 30, 30);
}

.config-field {
  margin-bottom: 1rem;
}

.json-field {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgb(30, 30, 30);
  font-size: 0.9rem;
  font-weight: 500;
}

.json-editor {
  width: 100%;
  min-height: 120px;
  padding: 0.75rem;
  background: #fff;
  border: 1px solid rgb(217, 217, 217);
  border-radius: 4px;
  color: rgb(30, 30, 30);
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
  color: #666;
  font-size: 0.75rem;
}
</style>
