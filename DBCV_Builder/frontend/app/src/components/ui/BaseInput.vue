<template>
  <div class="input-wrapper">
    <label v-if="label" :style="{ color: labelColor }" class="input-label">
      {{ label }}
      <span v-if="hint" :title="hint" class="hint-icon">[?]</span>
    </label>
    <input
      :class="[inputClass, { 'error-input': error }]"
      :disabled="disabled"
      :placeholder="placeholder"
      :type="type"
      v-model="model"
    />
    <span v-if="error" class="field-error">{{ error }}</span>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseInput',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
interface Props {
  type?: string;
  label?: string;
  labelColor?: string;
  placeholder?: string;
  hint?: string;
  inputClass?: string;
  disabled?: boolean;
  error?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  label: '',
  labelColor: 'rgb(255, 255, 255)',
  placeholder: '',
  hint: '',
  inputClass: 'input',
  disabled: false,
  error: '',
});

const model = defineModel<string>({ default: '' });
</script>

<style scoped>
.input-wrapper {
  width: 100%;
}

.input-label {
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  margin: 0 0 6px;
}

.input {
  border: 1px solid rgb(217, 217, 217);
  background-color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: normal;
  width: 100%;
}

.input:disabled {
  background-color: rgb(240, 240, 240);
  color: rgb(150, 150, 150);
  cursor: not-allowed;
  border-color: rgb(220, 220, 220);
}

.hint-icon {
  margin-left: 3px;
  cursor: pointer;
  font-size: 10px;
  vertical-align: middle;
  position: relative;
  top: -2px;
}

.hint-icon:hover {
  opacity: 0.8;
}

.input-wrapper.dark {
  display: grid;
  gap: 10px;
}

.dark .input-label {
  margin: 0;
}

.dark .input {
  margin: 0;
  border: none;
  background: #212121;
  color: #ffffff;
}

.dark .input:disabled {
  background-color: rgb(80, 80, 80);
  color: rgb(150, 150, 150);
  cursor: not-allowed;
}

.field-error {
  color: #dc3545;
  font-size: 12px;
  display: block;
}

.error-input {
  border-color: #dc3545 !important;
}
</style>
