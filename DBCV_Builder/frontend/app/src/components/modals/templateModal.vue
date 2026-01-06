<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal">
      <div class="modal-head">
        <div class="modal-title">{{ isEdit ? 'Редактировать шаблон' : 'Создать шаблон' }}</div>
        <button class="modal-close" @click="close">×</button>
      </div>
      <div v-if="isEdit && props.initial?.id" class="form-group id-group">
        <label>ID шаблона:</label>
        <BaseCopyableId :id="props.initial.id" />
      </div>
      <div v-if="isEdit && props.initial?.bot_id" class="form-group id-group">
        <label>ID агента шаблона:</label>
        <BaseCopyableId :id="props.initial.bot_id" />
      </div>
      <form @submit.prevent="handleSave">
        <BaseInput v-model="form.name" required label="Название *" class="dark" />
        <BaseInput v-model="form.description" label="Описание" class="dark" />
        <BaseSelect
          v-if="!props.botId"
          v-model="form.selectedBotId"
          :options="botsOptions"
          label="Выбрать агента *"
          label-color="#fff"
          class="dark"
          @update:model-value="updateAvailableSteps"
        />
        <div class="form-group">
          <label>Шаги (выберите шаги для шаблона) *</label>
          <div v-if="availableSteps.length === 0" class="no-steps">
            {{
              form.selectedBotId
                ? 'У выбранного агента нет шагов'
                : 'Выберите агента для загрузки шагов'
            }}
          </div>
          <div v-else class="custom-multiselect">
            <div class="select-list">
              <label v-for="step in availableSteps" :key="step.id" class="select-item">
                <BaseCheckbox v-model="form.step_ids" :value="step.id" variant="green" />
                <span>{{ step.name }}</span>
              </label>
            </div>
            <div v-if="form.step_ids.length" class="selected-steps">
              <span v-for="id in form.step_ids" :key="id" class="selected-step">
                {{ availableSteps.find((s) => s.id === id)?.name || id }}
              </span>
            </div>
          </div>
        </div>
        <BaseSelect
          v-model="form.first_step_id"
          :options="firstStepOptions"
          label="Первый шаг *"
          label-color="#fff"
          class="dark"
          :disabled="!form.step_ids.length"
        />
        <BaseCodeEditor
          :default-height="100"
          :is-collapsed="false"
          :is-resizable="false"
          v-model="form.variablesJson"
          label="Variables (JSON)"
          language="json"
          height="120px"
        />
        <div class="form-group">
          <label>Inputs</label>
          <JsonSchemaBuilder v-model="form.inputs" section-title="Inputs" />
        </div>
        <div class="form-group">
          <label>Outputs</label>
          <JsonSchemaBuilder v-model="form.outputs" section-title="Outputs" />
        </div>
        <div class="modal-footer">
          <button type="button" class="btn secondary" @click="close">Отмена</button>
          <button type="submit" class="btn primary" :disabled="isLoading">
            {{ isLoading ? 'Загрузка...' : isEdit ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineEmits, defineProps, onMounted } from 'vue';
import { useGeneratedEntityName } from '@/composables';
import { useBotsStore } from '@/stores';
import JsonSchemaBuilder from '@/components/ui/JsonSchemaBuilder.vue';

const props = defineProps({
  steps: { type: Array, default: () => [] },
  initial: { type: Object, default: null },
  botId: { type: String, default: null },
});

const emit = defineEmits(['close', 'save']);

const botsStore = useBotsStore();

const isEdit = computed(() => !!props.initial);
const isLoading = ref(false);

const form = ref({
  name: '',
  description: '',
  variablesJson: '{}',
  inputs: [],
  outputs: [],
  step_ids: [],
  first_step_id: '',
  selectedBotId: props.botId || '',
});

const availableSteps = ref([]);
const error = ref('');

const { generateName } = useGeneratedEntityName();

const botsOptions = computed(() => {
  const options = botsStore.bots.map((bot) => ({
    label: bot.name,
    value: bot.id,
  }));
  options.unshift({ label: 'Выберите агента', value: '' });
  return options;
});

const firstStepOptions = computed(() =>
  availableSteps.value
    .filter((s) => form.value.step_ids.includes(s.id))
    .map((s) => ({ label: s.name, value: s.id }))
);

const updateAvailableSteps = () => {
  if (!form.value.selectedBotId) {
    availableSteps.value = [];
    return;
  }

  const selectedBot = botsStore.bots.find((bot) => bot.id === form.value.selectedBotId);
  availableSteps.value = selectedBot?.steps || [];
};

onMounted(async () => {
  if (!props.botId && botsStore.bots.length === 0) {
    const response = await botsStore.readBots();
  }

  if (props.initial) {
    form.value.name = props.initial.name || '';
    form.value.description = props.initial.description || '';
    form.value.variablesJson = JSON.stringify(props.initial.variables || {}, null, 2);
    form.value.inputs = parseSchema(props.initial.inputs);
    form.value.outputs = parseSchema(props.initial.outputs);
    form.value.step_ids = Array.isArray(props.initial.steps)
      ? props.initial.steps.map((s) => s.id)
      : [];
    form.value.first_step_id = props.initial.first_step_id || '';

    if (props.botId) {
      form.value.selectedBotId = props.botId;
      availableSteps.value = props.steps;
    } else if (props.initial.bot_id) {
      form.value.selectedBotId = props.initial.bot_id;
      const response = await loadBotSteps();
    }
  } else {
    form.value.name = generateName('шаблон');

    if (props.botId) {
      form.value.selectedBotId = props.botId;
      availableSteps.value = props.steps;
    }
  }
});

watch(
  () => props.initial,
  async (val) => {
    if (val) {
      form.value.name = val.name || '';
      form.value.description = val.description || '';
      form.value.variablesJson = JSON.stringify(val.variables || {}, null, 2);
      form.value.inputs = parseSchema(val.inputs);
      form.value.outputs = parseSchema(val.outputs);
      form.value.step_ids = Array.isArray(val.steps) ? val.steps.map((s) => s.id) : [];
      form.value.first_step_id = val.first_step_id || '';

      if (props.initial.bot_id && !props.botId) {
        form.value.selectedBotId = props.initial.bot_id;
        const response = await loadBotSteps();
      }
    }
  }
);

function close() {
  emit('close');
}

function handleSave() {
  error.value = '';
  if (!form.value.name.trim()) {
    error.value = 'Название обязательно';
    return;
  }
  if (!props.botId && !form.value.selectedBotId) {
    error.value = 'Выберите агента';
    return;
  }
  if (!form.value.step_ids.length) {
    error.value = 'Выберите хотя бы один шаг';
    return;
  }

  if (!form.value.first_step_id) {
    error.value = 'Выберите первый шаг';
    return;
  }
  let variables;
  try {
    variables = JSON.parse(form.value.variablesJson || '{}');
  } catch {
    error.value = 'Variables должны быть валидным JSON';
    return;
  }

  emit('save', {
    name: form.value.name,
    description: form.value.description,
    variables,
    inputs: buildSchema(form.value.inputs),
    outputs: buildSchema(form.value.outputs),
    step_ids: Array.isArray(form.value.step_ids) ? form.value.step_ids : [form.value.step_ids],
    first_step_id: form.value.first_step_id,
    bot_id: props.botId || form.value.selectedBotId,
  });
}

function buildSchema(fields) {
  const schema = { type: 'object', properties: {}, required: [] };
  for (const f of fields) {
    const prop = { type: f.type };
    if (f.default !== '') prop.default = f.default;
    if (f.description) prop.description = f.description;
    if (f.type === 'object') {
      const nestedSchema = buildSchema(f.properties);
      prop.properties = nestedSchema.properties;
      if (nestedSchema.required && nestedSchema.required.length > 0) {
        prop.required = nestedSchema.required;
      }
    }
    schema.properties[f.name] = prop;
    if (f.required) schema.required.push(f.name);
  }
  return schema;
}

function parseSchema(schema) {
  if (!schema || !schema.properties) return [];
  return Object.entries(schema.properties).map(([name, prop]) => {
    const base = {
      id: name + '-' + Math.random().toString(36).slice(2, 8),
      name,
      type: prop.type,
      required: Array.isArray(schema.required) ? schema.required.includes(name) : false,
      default: prop.default ?? '',
      description: prop.description ?? '',
      properties: [],
      items: [],
    };
    if (prop.type === 'object') base.properties = parseSchema(prop);
    if (prop.type === 'array')
      base.items = prop.items
        ? parseSchema({ type: 'object', properties: { item: prop.items }, required: [] })
        : [];
    return base;
  });
}
</script>

<style scoped>
* {
  text-transform: none;
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
}

.modal-overlay {
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow: auto;
  padding: 30px 0;
}

.modal {
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
  padding: 10px 15px;
  min-width: 300px;
  width: 100%;
  max-width: 90vw;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.modal-title {
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}

form {
  display: grid;
  gap: 10px;
}

.input-wrapper.dark,
.resizable-editor,
.form-group {
  display: grid;
  gap: 5px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn.primary {
  background: #4caf50;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 15px;
}

.btn.secondary {
  background: #eee;
  color: #333;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 15px;
  cursor: pointer;
}

.error {
  color: #d32f2f;
  margin-top: 10px;
}

.custom-multiselect {
  background: #212121;
  border-radius: 8px;
  padding: 8px;
}

.select-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.select-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  background: #313131;
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.select-item:hover {
  background: #4caf505c;
}

.selected-steps {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.selected-step {
  background: #4caf50;
  color: #fff;
  border-radius: 4px;
  padding: 2px 8px;
}

.id-group {
  display: flex;
  position: relative;
  top: -10px;
}
</style>
