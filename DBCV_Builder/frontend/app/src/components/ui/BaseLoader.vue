<template>
  <div class="loader">
    <LoaderIcon />
    Загрузка...
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseLoader',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
//@ts-ignore
import { LoaderIcon } from '@/components/icons';
</script>

<style scoped>
.loader {
  align-items: center;
  display: flex;
  flex-wrap: nowrap;
  gap: 0.5em;
  justify-content: center;
}
</style>
