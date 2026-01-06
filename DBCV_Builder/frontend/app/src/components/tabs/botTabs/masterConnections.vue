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
            :default-height="200"
            v-model="block.textareaValue"
            @input="isSomethingChangedArr[index] = true"
            class="code-editor"
            light-theme
            small
          />
        </div>
        <div v-if="block.selectedOption === 'response'">
          <BaseSelect
            v-model="block.inputValue"
            :options="requestsOptions"
            :label="'Запрос'"
            :labelColor="'rgb(30, 30, 30)'"
            @update:model-value="isSomethingChanged[index] = true"
          />
        </div>
        <!-- Раздел "Сохранить как" -->
        <div class="save-as-section">
          <span class="label">Сохранить как</span>
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
          <button @click="addSaveAsRow(index)">Добавить строку</button>
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
              <div class="move-btns">
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
              <button @click="removeConnection(index, connectionIndex)">
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
        <div class="move-btns">
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
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue';
import { BottomArrowIcon, TopArrowIcon, TrashIcon } from '@/components/icons'; // импорт иконок
import { useBotsStore, useConnectionGroupsStore, useRequestsStore } from '@/stores'; // импорт stores
import notyf from '@/plugins/notyf';

const props = defineProps({
  botId: {
    type: String,
    required: true,
  },
  botInfo: {
    type: Object,
  },
});

const botStore = useBotsStore();
const requestsStore = useRequestsStore();
const connectionGroupsStore = useConnectionGroupsStore();

const blocks = ref([]);
const requestsOptions = ref([]);
const nodes = inject('nodes');

const isSomethingChangedArr = ref(Array.from({ length: blocks?.length ?? 0 }).fill(false));

const isSomethingChanged = computed(() => {
  return isSomethingChangedArr.value.indexOf(true) !== -1;
});

// Код для Connection-Group
const addConnectionGroup = async () => {
  const newGroupData = {
    search_type: 'message',
    priority: blocks.value.length,
    code: null,
    request_id: null,
    variables: null,
    bot_id: props.botId,
    connections: [],
  };

  const response = await connectionGroupsStore.createConnectionGroup(newGroupData);

  blocks.value.push({
    id: response.id,
    selectedOption: 'message',
    textareaValue: '',
    inputValue: '',
    saveAsRows: [{ left: '', right: '' }],
    connections: [],
  });
};

const removeConnectionGroup = async (index) => {
  const blockToRemove = blocks.value[index];

  if (!blockToRemove.id) {
    console.warn('Невозможно удалить группу без ID');
    return;
  }

  await connectionGroupsStore.deleteConnectionGroup(blockToRemove.id);
  blocks.value.splice(index, 1);
};

const moveUp = (index) => {
  if (index > 0) {
    isSomethingChangedArr.value[index] = true;
    isSomethingChangedArr.value[index - 1] = true;
    [blocks.value[index - 1], blocks.value[index]] = [blocks.value[index], blocks.value[index - 1]];
  }
};

const moveDown = (index) => {
  if (index < blocks.value.length - 1) {
    isSomethingChangedArr.value[index] = true;
    isSomethingChangedArr.value[index + 1] = true;
    [blocks.value[index + 1], blocks.value[index]] = [blocks.value[index], blocks.value[index + 1]];
  }
};

// // Код для Connection
const addConnection = (blockIndex) => {
  isSomethingChangedArr.value[blockIndex] = true;
  const defaultOption = connectionOptions.value[0]?.value || '';
  blocks.value[blockIndex].connections.push({
    type: defaultOption,
    rules: '',
  });
};

const removeConnection = (blockIndex, connectionIndex) => {
  isSomethingChangedArr.value[blockIndex] = true;
  blocks.value[blockIndex].connections.splice(connectionIndex, 1);
};

const moveConnectionUp = (blockIndex, connectionIndex) => {
  isSomethingChangedArr.value[blockIndex] = true;
  if (connectionIndex > 0) {
    const connections = blocks.value[blockIndex].connections;
    [connections[connectionIndex - 1], connections[connectionIndex]] = [
      connections[connectionIndex],
      connections[connectionIndex - 1],
    ];
  }
};

const moveConnectionDown = (blockIndex, connectionIndex) => {
  isSomethingChangedArr.value[blockIndex] = true;
  if (connectionIndex < blocks.value[blockIndex].connections.length - 1) {
    const connections = blocks.value[blockIndex].connections;
    [connections[connectionIndex + 1], connections[connectionIndex]] = [
      connections[connectionIndex],
      connections[connectionIndex + 1],
    ];
  }
};

// // Метод для добавления строки в раздел "Сохранить как"
const addSaveAsRow = (blockIndex) => {
  isSomethingChangedArr.value[blockIndex] = true;
  blocks.value[blockIndex].saveAsRows.push({ left: '', right: '' });
};

// // Наполнение селектов
const options = [
  { value: 'code', label: 'Код' },
  { value: 'response', label: 'Request' },
  { value: 'message', label: 'Message' },
  { value: 'integration', label: 'Integration' },
];

const connectionOptions = computed(() => {
  return nodes.value.map((node) => ({
    value: node.id,
    label: node.data.name || `Узел ${node.id}`,
  }));
});

// // Клик по кнопке "сохранить"
const saveData = async (blockIndex) => {
  const block = blocks.value[blockIndex];

  const variables = block.saveAsRows.reduce((acc, row) => {
    if (row.left && row.right) {
      acc[row.left] = row.right;
    }
    return acc;
  }, {});

  const connections = block.connections.map((connection, index) => ({
    next_step_id: connection.type,
    rules: connection.rules || '',
    priority: index,
    filters: null,
  }));

  const connectionGroupData = {
    id: block.id,
    search_type: block.selectedOption,
    priority: blockIndex,
    code: block.selectedOption === 'code' ? block.textareaValue : null,
    request_id: block.selectedOption === 'response' ? block.inputValue : null,
    variables: JSON.stringify(variables),
    connections: connections,
  };

  isSomethingChangedArr.value[blockIndex] = false;

  await connectionGroupsStore.updateConnectionGroup(connectionGroupData.id, connectionGroupData);
  notyf.success('Сохранено!');
};

const save = async () => {
  for (let i = 0; i < blocks.value.length; i++) await saveData(i);
  isSomethingChangedArr.value = isSomethingChangedArr.value.fill(false);
};

// // Показывать существующие Connection group
const initializeBlocks = async () => {
  const response = await botStore.readBot(props.botId);
  const masterConnections = response?.data.master_connection_groups || [];
  if (masterConnections.length > 0) {
    blocks.value = masterConnections.map((group) => {
      const parsedVariables = group.variables ? JSON.parse(group.variables) : {};
      return {
        id: group.id,
        selectedOption: group.search_type,
        textareaValue: group.code || '',
        inputValue: group.request_id || '',
        saveAsRows: Object.entries(parsedVariables).map(([key, value]) => ({
          left: key,
          right: value,
        })),
        connections: group.connections.map((connection) => ({
          type: connection.next_step_id,
          rules: connection.rules || '',
        })),
      };
    });
  }
};

onMounted(async () => {
  initializeBlocks();
  await requestsStore.readRequests();
  requestsOptions.value = requestsStore.requests.map((request) => ({
    value: request.id,
    label: request.name || `Реквест ${request.id}`,
  }));
});

defineExpose({ isSomethingChanged, save });
</script>

<style scoped>
* {
  text-transform: none;
}

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
</style>
