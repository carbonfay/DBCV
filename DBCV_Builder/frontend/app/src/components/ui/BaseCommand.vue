<template>
  <span>{{ commandHelp }}</span>
</template>

<script lang="ts">
export default {
  name: 'BaseCommand',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script lang="ts" setup>
import { computed } from 'vue';

const props = defineProps<{
  command: string;
}>();

const commandHelp = computed(() => {
  if (navigator.platform.toLowerCase().includes('mac')) {
    return `⌘ + ${props.command}`;
  }
  return `Ctrl + ${props.command}`;
});
</script>

<style scoped>
span {
  display: inline-block;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.2;
  color: #8b8b8b;
}
</style>
