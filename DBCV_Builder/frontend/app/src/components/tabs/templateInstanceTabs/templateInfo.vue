<template>
  <div class="flex">
    <div class="section">
      <div class="template-details">
        <div class="detail-item">
          <label>template_instance_id:</label>
          <BaseCopyableId :id="props.node.data.template_id" />
        </div>
        <div class="detail-item">
          <BaseInput
            v-model="editableNode.name"
            :label="'Название шаблона:'"
            class="section-input"
            @input="isSomethingChanged = true"
          />
        </div>
      </div>
    </div>
    <div class="section">
      <div class="mapping-info">
        <div class="mapping-item">
          <label>Inputs Mapping:</label>
          <pre class="mapping-json">{{ formatJson(props.node.data.inputs_mapping) }}</pre>
        </div>
        <div class="mapping-item">
          <label>Outputs Mapping:</label>
          <pre class="mapping-json">{{ formatJson(props.node.data.outputs_mapping) }}</pre>
        </div>
      </div>
    </div>
    <BaseButton styleType="secondary" size="small" type="submit" class="button" @click="save">
      Сохранить
    </BaseButton>
  </div>
</template>

<script setup>
import { defineProps, ref } from 'vue';
import notyf from '@/plugins/notyf';

const isSomethingChanged = ref(false);

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const editableNode = ref({
  name: props.node.data.name || '',
  id: props.node.id,
  type: props.node.type,
});

const emit = defineEmits(['update-node']);

const save = async () => {
  emit('update-node', editableNode.value);
  notyf.success('Сохранено!');
  isSomethingChanged.value = false;
};

const formatJson = (obj) => {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
};

defineExpose({ isSomethingChanged, save });
</script>

<style scoped>
.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 193, 7);
  margin-bottom: 10px;
}

.template-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-name {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.mapping-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mapping-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mapping-item label,
.detail-item label {
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  margin: 0;
  color: #fff;
}

.mapping-json {
  font-size: 12px;
  font-family: monospace;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
  max-height: 180px;
  overflow: auto;
}

.section-checkbox {
  margin: 10px 0;
}

.flex {
  display: flex;
  flex-direction: column;
}

.flex .button {
  align-self: flex-end;
}
</style>
