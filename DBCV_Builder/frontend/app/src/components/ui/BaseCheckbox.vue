<template>
  <label class="custom-checkbox">
    <input type="checkbox" :checked="isChecked" @change="onChange" :disabled="disabled" />
    <span :class="['checkbox-indicator', variant === 'green' ? 'green' : '']"></span>
    <span class="checkbox-label" :style="{ color: labelColor }">
      <slot />
    </span>
  </label>
</template>

<script lang="ts">
export default {
  name: 'BaseCheckbox',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  value?: string | number | boolean;
  labelColor?: string;
  variant?: 'default' | 'green';
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  value: undefined,
  labelColor: 'rgb(34, 34, 34)',
  variant: 'default',
  disabled: false,
});

type Model = boolean | Array<string | number | boolean>;

const model = defineModel<Model>({ default: false });

const isChecked = computed(() => {
  if (props.value !== undefined) {
    return Array.isArray(model.value) && model.value.includes(props.value);
  } else {
    return !!model.value;
  }
});

function onChange(e: Event) {
  if (props.disabled) return;
  const target = e.target as HTMLInputElement;
  if (props.value !== undefined) {
    let arr = Array.isArray(model.value) ? [...model.value] : [];
    if (target.checked) {
      if (!arr.includes(props.value)) arr.push(props.value);
    } else {
      arr = arr.filter((v) => v !== props.value);
    }
    model.value = arr;
  } else {
    model.value = target.checked;
  }
}
</script>

<style scoped>
.custom-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.custom-checkbox input {
  display: none;
}

.checkbox-indicator {
  width: 16px;
  height: 16px;
  border: 2px solid rgb(34, 34, 34);
  border-radius: 4px;
  display: inline-block;
  margin-right: 8px;
  position: relative;
  transition:
    background-color 0.3s,
    border-color 0.3s;
}

.custom-checkbox input:checked + .checkbox-indicator {
  background-color: rgb(34, 34, 34);
  border-color: rgb(34, 34, 34);
}

.custom-checkbox .checkbox-indicator.green {
  border-color: #4caf50;
}

.custom-checkbox input:checked + .checkbox-indicator.green {
  background-color: #4caf50;
  border-color: #4caf50;
}

.checkbox-indicator::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0);
  width: 8px;
  height: 4px;
  border: 2px solid white;
  border-top: none;
  border-right: none;
  transform-origin: center;
  opacity: 0;
  transition:
    transform 0.3s,
    opacity 0.3s;
}

.custom-checkbox input:checked + .checkbox-indicator::after {
  transform: translate(-50%, -50%) rotate(-45deg) scale(1);
  opacity: 1;
}

.checkbox-label {
  font-size: 14px;
  color: rgb(44, 44, 44);
  letter-spacing: 0.03em;
}

.custom-checkbox input:disabled + .checkbox-indicator {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
