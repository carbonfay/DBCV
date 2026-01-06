<template>
  <div class="filters-block">
    <div class="sort-buttons">
      <button
        v-for="option in options"
        :key="option.value"
        :class="{ active: modelValue === option.value }"
        @click="modelValue = option.value"
      >
        {{ option.label }}
      </button>
    </div>
    <div v-if="isSearch" class="sort-input">
      <BaseInput v-model="searchQuery" class="dark" placeholder="Поиск" />
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseSortButtons',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
interface SortOption {
  value: string;
  label: string;
}

interface Props {
  options: SortOption[];
  isSearch?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isSearch: false,
});

const modelValue = defineModel<string>();
const searchQuery = defineModel<string>('searchQuery', { default: '' });
</script>

<style scoped>
.filters-block {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 20px 0;
  width: 100%;
}

button {
  font-size: 16px;
  line-height: 1.4;
  color: #fff;
  padding: 5px 10px;
  border-radius: 10px;
  transition: background-color 0.3s;
}

button:hover,
button:active,
button.active {
  background: rgb(49, 49, 49);
}
</style>
