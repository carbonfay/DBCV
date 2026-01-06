<template>
  <div class="custom-select" v-click-outside="closeDropdown">
    <label v-if="label" class="select-label" :style="{ color: labelColor }" @click="closeDropdown">
      {{ label }}
    </label>
    <button type="button" class="select-button" @click="toggleDropdown">
      {{ selectedLabel || placeholder }}
    </button>
    <div v-if="isOpen" class="dropdown">
      <input type="text" v-model="searchQuery" placeholder="Поиск..." class="search-input" />
      <ul class="options-list">
        <li
          v-for="option in filteredOptions"
          :key="option.value"
          @click="selectOption(option)"
          class="option-item"
        >
          {{ option.label }}
        </li>
        <li v-if="filteredOptions.length === 0" class="no-results">Ничего не найдено</li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseSelectSearch',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Option } from '@/types/component_types';

interface Props {
  options: Option[];
  placeholder?: string;
  label?: string;
  labelColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [],
  placeholder: '',
  label: '',
  labelColor: 'rgb(30, 30, 30)',
});

const model = defineModel<string | number | null>({ default: null });

const emit = defineEmits<{
  (e: 'input'): void;
}>();

const searchQuery = ref('');
const isOpen = ref(false);

const filteredOptions = computed(() => {
  return props.options.filter((option) =>
    option.label.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const selectedLabel = computed(() => {
  const selectedOption = props.options.find((option) => option.value === model.value);
  return selectedOption?.label || '';
});

const selectOption = (option: Option) => {
  model.value = option.value;
  emit('input');
  searchQuery.value = '';
  isOpen.value = false;
};

const toggleDropdown = () => {
  isOpen.value = !isOpen.value;
};

const closeDropdown = (event?: Event) => {
  if (event) {
    const target = event.target as HTMLElement;

    if (target.closest('.select-button') || target.closest('.dropdown')) {
      return;
    }
  }

  if (isOpen.value) {
    isOpen.value = false;
  }
};
</script>

<style scoped>
.custom-select {
  position: relative;
  width: 100%;
}

.select-label {
  display: block;
  width: 100%;
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  margin: 0;
}

.select-button {
  position: relative;
  width: 100%;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.3s;
  appearance: none;
  border: 1px solid rgb(217, 217, 217);
  background-color: #fff;
  border-radius: 8px;
  padding: 8px 28px 8px 14px;
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: normal;
  min-height: 34px;
  word-break: break-word;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  border: 1px solid rgb(217, 217, 217);
  border-radius: 4px;
  background: white;
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.search-input {
  width: 100%;
  padding: 8px;
  outline: none;
  color: rgb(30, 30, 30);
  border: 0;
  border-bottom: 1px solid rgb(217, 217, 217);
  background: #fff;
}

.options-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.option-item {
  padding: 4px 8px;
  cursor: pointer;
  color: rgb(30, 30, 30);
  font-size: 14px;
  font-weight: 400;
}

.option-item:hover {
  background-color: rgb(217, 217, 217);
}

.no-results {
  padding: 4px 8px;
  color: rgb(30, 30, 30);
  text-align: center;
  font-size: 14px;
  font-weight: 400;
}

.custom-select.dark {
  gap: 10px;
  display: grid;
}

.dark .select-button {
  border: none;
  background: #212121;
  color: #ffffff;
}

.dark .search-input {
  background: #212121;
  color: #ffffff;
}

.dark .option-item  {
  color: rgba(255, 255, 255, 0.8);
  background: #212121;
}

.dark .option-item:hover {
  background: #25282c;
}

.dark .dropdown {
  border: 1px solid #25282c;
}

.dark .no-results {
  color: rgba(255, 255, 255, 0.8);
  background: #212121;
  padding: 10px 0;
}
</style>
