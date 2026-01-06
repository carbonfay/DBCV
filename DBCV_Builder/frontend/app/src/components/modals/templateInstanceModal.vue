<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal">
      <div class="modal-head">
        <div class="modal-title">Создать инстанс шаблона: {{ template?.name }}</div>
        <button class="modal-close" @click="close">×</button>
      </div>
      <div class="form-group id-group">
        <label>ID шаблона:</label>
        <BaseCopyableId :id="template.id" />
      </div>
      <form @submit.prevent="handleSave">
        <div class="form-group">
          <BaseCodeEditor
            :default-height="100"
            :is-collapsed="false"
            :is-resizable="false"
            v-model="form.variablesJson"
            label="Variables (JSON)"
            language="json"
            height="120px"
          />
        </div>
        <div class="form-group">
          <label>Inputs Mapping</label>
          <MappingBuilder v-model="inputsMapping" section-title="Inputs Mapping" />
        </div>
        <div class="form-group">
          <label>Outputs Mapping</label>
          <MappingBuilder v-model="outputsMapping" section-title="Outputs Mapping" />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn secondary" @click="close">Отмена</button>
          <button type="submit" class="btn primary">Создать</button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineEmits, defineProps, onMounted } from 'vue';
import MappingBuilder from '@/components/ui/MappingBuilder.vue';

const props = defineProps({
  template: { type: Object, required: true },
  botId: { type: String, required: true },
});
const emit = defineEmits(['close', 'save']);

const form = ref({
  variablesJson: '{}',
});
const error = ref('');

const inputsMapping = ref(parseSchema(props.template.inputs));
const outputsMapping = ref(parseSchema(props.template.outputs));

onMounted(() => {
  if (props.template) {
    form.value.variablesJson = JSON.stringify(props.template.variables || {}, null, 2);
  }
});

watch(
  () => props.template,
  (val) => {
    if (val) {
      form.value.variablesJson = JSON.stringify(val.variables || {}, null, 2);
      inputsMapping.value = parseSchema(val.inputs);
      outputsMapping.value = parseSchema(val.outputs);
    }
  },
  { immediate: true }
);

function close() {
  emit('close');
}

function buildMapping(fields, parentPath = '') {
  const result = {};
  for (const field of fields) {
    const pathValue = field.value && field.value.trim() !== '' ? field.value : null;
    if (field.type === 'object') {
      result[field.name] = buildMapping(field.properties, pathValue);
    } else {
      result[field.name] = {
        path: pathValue,
        default: field.default,
        value: field.value,
      };
    }
  }
  return result;
}

function handleSave() {
  error.value = '';
  let variables;
  try {
    variables = JSON.parse(form.value.variablesJson || '{}');
  } catch {
    error.value = 'Variables должны быть валидным JSON';
    return;
  }
  emit('save', {
    template_id: props.template.id,
    inputs_mapping: buildMapping(inputsMapping.value),
    outputs_mapping: buildMapping(outputsMapping.value),
    variables,
    bot_id: props.botId,
  });
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
    };
    if (prop.type === 'object') base.properties = parseSchema(prop);
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

.form-group {
  margin-bottom: 16px;
}

.input {
  width: 100%;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 15px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
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

.id-group {
  display: flex;
  position: relative;
  top: -10px;
}
</style>
