<template>
  <div class="mcp-drawer">
    <AutonomousAssistant :bot-id="botId" />
  </div>
</template>

<script setup lang="ts">
import AutonomousAssistant from '@/components/autonomousAssistant.vue';

defineProps<{ botId?: string }>();
</script>

<style scoped>
.mcp-drawer {
  height: 100%;
  overflow-y: auto;
  background: #0b0b0d;
  color: #f5f5f5;
}
</style>
