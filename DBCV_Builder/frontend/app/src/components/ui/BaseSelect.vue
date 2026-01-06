<template>
  <div class="custom-select-wrapper">
    <label v-if="label" class="select-label" :style="{ color: labelColor }">{{ label }}</label>
    <select v-model="model" class="custom-select">
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <div class="custom-arrow">∨</div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseSelect',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import type { Option } from '@/types/component_types';

interface Props {
  options?: Option[];
  label?: string;
  labelColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [],
  label: '',
  labelColor: 'rgb(30, 30, 30)',
});

const model = defineModel<string | number>();
</script>

<style scoped>
.custom-select-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.select-label {
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  margin: 0;
}

.custom-select {
  position: relative;
  appearance: none;
  border: 1px solid rgb(217, 217, 217);
  background-color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: normal;
  width: 100%;
  padding: 8px 28px 8px 14px;
}

.custom-arrow {
  position: absolute;
  right: 12px;
  bottom: 15%;
  pointer-events: none;
  font-size: 14px;
  color: #333;
}

.custom-select option {
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: normal;
}

.custom-select-wrapper.dark {
  gap: 10px;
}

.dark .custom-select {
  border: none;
  background: #212121;
  color: #ffffff;
}

.dark option {
  color: #ffffff;
}
</style>
