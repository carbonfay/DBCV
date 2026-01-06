<template>
  <div class="flex">
    <Tab3 :node="props.node" @graphUpdate-node="$emit('graphUpdate-node', $event)" />
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import Tab3 from '@/components/tabs/nodeTabs/tab3.vue';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

defineEmits(['graphUpdate-node']);
</script>

<style scoped>
.flex {
  display: flex;
  flex-direction: column;
}
</style>
