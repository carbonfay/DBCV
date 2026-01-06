<template>
  <div class="json-schema-builder">
    <table class="schema-table">
      <thead>
        <tr>
          <th>properties</th>
          <th>type</th>
          <th>required</th>
          <th>default</th>
          <th>description</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(field, idx) in fields" :key="field.id">
          <tr>
            <td>
              <input v-model="field.name" placeholder="name" class="input" />
            </td>
            <td>
              <select v-model="field.type" class="input">
                <option value="string">string</option>
                <option value="number">number</option>
                <option value="boolean">boolean</option>
                <option value="object">object</option>
              </select>
            </td>
            <td>
              <BaseCheckbox v-model="field.required" />
            </td>
            <td>
              <input v-if="field.type !== 'object'" v-model="field.default" class="input" />
            </td>
            <td>
              <input v-model="field.description" class="input" />
            </td>
            <td>
              <button type="button" @click="removeField(idx)" class="remove-btn">x</button>
            </td>
          </tr>
          <tr v-if="field.type === 'object'">
            <td colspan="6" class="nested">
              <JsonSchemaBuilder
                v-model="field.properties"
                :is-root="false"
                section-title="Object properties"
              />
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <button type="button" @click="addField" class="add-btn">добавить</button>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits, watch } from 'vue';
import { nanoid } from 'nanoid';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  sectionTitle: { type: String, default: 'Section 1' },
});
const emit = defineEmits(['update:modelValue']);

const fields = ref(props.modelValue.map((f) => ({ ...f, id: f.id || nanoid() })));

function addField() {
  fields.value.push({
    id: nanoid(),
    name: '',
    type: 'string',
    required: false,
    default: '',
    description: '',
    properties: [],
    items: [],
  });
  emit('update:modelValue', fields.value);
}

function removeField(idx) {
  fields.value.splice(idx, 1);
  emit('update:modelValue', fields.value);
}

watch(
  () => props.modelValue,
  (val) => {
    if (val.length !== fields.value.length || val.some((f, i) => f.id !== fields.value[i]?.id)) {
      fields.value = val.map((f) => ({ ...f, id: f.id || nanoid() }));
    }
  }
);

watch(
  fields,
  (val) => {
    emit('update:modelValue', val);
  },
  { deep: true }
);
</script>

<style scoped>
* {
  color: #fff;
}

.json-schema-builder {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px;
  background: #313131;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.schema-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}

.schema-table th,
.schema-table td {
  padding: 4px 8px;
  font-size: 13px;
  text-align: left;
  color: #717171;
}

.input {
  width: 100%;
  padding: 6px 10px;
  border-radius: 4px;
  border: 0;
  background: #212121;
}

.add-btn {
  background: #4caf50;
  border-radius: 4px;
  padding: 2px 8px;
  margin-left: 8px;
}

.remove-btn {
  background: #f44336;
  border-radius: 4px;
  padding: 4px 8px;
}

.nested {
  background: #313131;
  padding: 8px;
}
</style>
