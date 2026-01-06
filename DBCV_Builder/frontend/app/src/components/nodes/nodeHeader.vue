<template>
  <div class="header">
    <slot name="icon">
      <CodeIcon v-if="showIcon" class="icon" />
    </slot>
    <span>{{ title }}</span>
  </div>
</template>

<script setup>
import { CodeIcon } from '@/components/icons'; // импорт иконок

defineProps({
  title: {
    type: String,
    required: true,
  },
  showIcon: {
    type: Boolean,
    default: true,
  },
});
</script>

<style scoped>
div {
  padding: 13px 0 3px;
}

.header {
  font-size: 10px;
  font-weight: 800;
  line-height: 13px;
  text-align: left;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.header span {
  color: rgb(199, 199, 199);
  word-break: break-word;
}

.icon {
  width: auto;
  height: 15px;
  margin-right: 8px;
}
</style>
