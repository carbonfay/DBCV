<template>
  <div class="mapping-builder">
    <table class="mapping-table">
      <thead>
        <tr>
          <th>name</th>
          <th>type</th>
          <th>required</th>
          <th>description</th>
          <th>default</th>
          <th>path</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(field, idx) in fields" :key="field.id">
          <tr>
            <td>{{ field.name }}</td>
            <td>{{ field.type }}</td>
            <td><BaseCheckbox v-model="field.required" disabled /></td>
            <td class="description-cell" :title="field.description">{{ field.description }}</td>
            <td>
              <BaseInput v-if="field.type !== 'object'" v-model="field.default" class="dark" />
            </td>
            <td>
              <BaseInput v-if="field.type !== 'object'" v-model="field.value" class="dark" />
            </td>
          </tr>
          <tr v-if="field.type === 'object'">
            <td colspan="6" class="nested">
              <MappingBuilder v-model="field.properties" :parentPath="getPath(field)" />
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch } from 'vue';
import { nanoid } from 'nanoid';
import MappingBuilder from '@/components/ui/MappingBuilder.vue';

defineOptions({ name: 'MappingBuilder' });

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  parentPath: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue']);

const fields = ref(
  props.modelValue.map((f) => ({ ...f, id: f.id || nanoid(), value: f.value ?? '' }))
);

watch(
  fields,
  (val) => {
    emit('update:modelValue', val);
  },
  { deep: true }
);

function getPath(field) {
  return props.parentPath ? `${props.parentPath}.${field.name}` : field.name;
}
</script>

<style scoped>
.mapping-builder {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px;
  background: #313131;
}

.mapping-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}

.mapping-table th,
.mapping-table td {
  padding: 4px 8px;
  font-size: 13px;
  text-align: left;
  color: #717171;
}

.mapping-table td {
  color: #fff;
}

.input {
  width: 100%;
  padding: 6px 10px;
  border-radius: 4px;
  border: 0;
  background: #212121;
}

.nested {
  background: #313131;
  padding: 8px;
}

.mapping-table input[type='checkbox'][disabled] {
  accent-color: #4caf50 !important;
  opacity: 1 !important;
}

.mapping-table td.description-cell {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
