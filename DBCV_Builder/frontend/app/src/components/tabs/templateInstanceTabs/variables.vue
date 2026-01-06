<template>
  <div class="flex">
    <div class="section">
      <p class="section-description">
        Отредактируйте переменные, которые будут использоваться этим экземпляром шаблона.
      </p>
      <BaseCodeEditor
        v-model="variablesJson"
        :default-height="300"
        :is-collapsed="false"
        :is-resizable="true"
        label="Variables (JSON)"
        language="json"
        height="300px"
        @input="isSomethingChanged = true"
      />
    </div>
    <div class="section">
      <div class="validation-info">
        <div v-if="validationError" class="validation-error">
          <span class="error-icon">⚠</span>
          {{ validationError }}
        </div>
        <div v-else class="validation-success">
          <span class="success-icon">✓</span>
          Valid JSON format
        </div>
      </div>
    </div>
    <BaseButton styleType="secondary" size="small" type="submit" class="button" @click="save">
      Сохранить
    </BaseButton>
  </div>
</template>

<script setup>
import { defineProps, ref, watch } from 'vue';
import notyf from '@/plugins/notyf';

const isSomethingChanged = ref(false);
const validationError = ref('');

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const variablesJson = ref(JSON.stringify(props.node.data.variables || {}, null, 2));

const emit = defineEmits(['update-node']);

watch(variablesJson, (newValue) => {
  try {
    JSON.parse(newValue);
    validationError.value = '';
  } catch (error) {
    validationError.value = 'Invalid JSON format';
  }
});

const save = async () => {
  try {
    const variables = JSON.parse(variablesJson.value);
    emit('update-node', {
      ...props.node,
      variables,
      template_instance_id: props.node.data.template_id,
      id: props.node.id,
      type: props.node.type,
    });
    notyf.success('Переменные сохранены!');
    isSomethingChanged.value = false;
  } catch (error) {
    notyf.error('Invalid JSON format');
  }
};

defineExpose({ isSomethingChanged, save });
</script>

<style scoped>
.section {
  margin-bottom: 20px;
}

.section-description {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 15px;
  line-height: 1.2;
}

.validation-info {
  padding: 10px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
}

.validation-error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff6b6b;
  font-size: 11px;
}

.validation-success {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4caf50;
  font-size: 11px;
}

.error-icon {
  font-size: 14px;
}

.success-icon {
  font-size: 14px;
}

.flex {
  display: flex;
  flex-direction: column;
}

.flex .button {
  align-self: flex-end;
}
</style>
