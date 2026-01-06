<template>
  <button :class="['custom-button', buttonSize, buttonStyle]" :disabled="disabled" :type="type">
    <slot />
  </button>
</template>

<script lang="ts">
export default {
  name: 'BaseButton',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  type?: 'button' | 'submit' | 'reset';
  size?: 'small' | 'medium' | 'large';
  styleType?: 'primary' | 'secondary' | 'danger' | 'danger-dark';
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'button',
  size: 'medium',
  styleType: 'primary',
  disabled: false,
});

const buttonSize = computed(() => `button--${props.size}`);
const buttonStyle = computed(() => `button--${props.styleType}`);
</script>

<style scoped>
.custom-button {
  border-radius: 6px;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.button--small {
  font-size: 12px;
  padding: 8px;
}

.button--medium {
  font-size: 16px;
  padding: 10px 12px;
}

.button--large {
  font-size: 20px;
  padding: 12px 20px;
}

.button--primary {
  border: 1px solid rgb(44, 44, 44);
  background: rgb(44, 44, 44);
  color: rgb(245, 245, 245);
}

.button--secondary {
  border: 1px solid rgb(74, 74, 74);
  background: rgb(44, 44, 44);
  color: rgb(245, 245, 245);
}

.button--danger {
  background-color: #dc3545;
  border: 1px solid #dc3545;
  color: white;
}

.button--danger-dark {
  background-color: #bc2e48;
  border: 1px solid #bc2e48;
  color: white;
}

.custom-button:disabled {
  background-color: #e0e0e0;
  color: #7a7a7a;
  cursor: not-allowed;
}
</style>
