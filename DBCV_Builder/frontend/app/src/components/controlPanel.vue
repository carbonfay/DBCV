<script lang="ts" setup>
// @ts-ignore
import { CloseIcon, FullScreenIcon, TrashIcon } from '@/components/icons';
import { computed, inject, onMounted, ref } from 'vue';

const { asideWidth } = defineProps<{ asideWidth: string }>();

// @ts-ignore
const { setDrawer, drawerRef, drawerProps } = inject('drawer');
const isFullScreen = ref(false);
const isClickOutsideEnabled = ref(false);

const emit = defineEmits(['action']);

const isMcpDrawer = computed(() => {
  const name = drawerRef.value?.$options?.__name;
  return name === 'McpPrompt' || name === 'AutonomousAssistant';
});

const close = async () => {
  if (!drawerProps.value?.group && drawerRef.value?.save && typeof drawerRef.value.save === 'function') {
    await drawerRef.value.save();
  }
  setDrawer(null);
};
const handleClickOutside = () => {
  if (isClickOutsideEnabled.value && !isMcpDrawer.value) {
    close();
  }
};

const deleteStep = () => {
  if (drawerProps.value?.node) {
    const node = drawerProps.value.node;
    const isConfirmed = window.confirm('Вы уверены, что хотите удалить этот узел?');
    if (isConfirmed) {
      emit('action', {
        action: 'delete',
        data: {
          id: node.id,
          type: node.type,
        },
      });
      close();
    }
  }
};

onMounted(() => {
  setTimeout(() => {
    isClickOutsideEnabled.value = true;
  }, 100);
});

// Определения заголовка
const getDrawerTitle = () => {
  if (drawerProps.value?.group) {
    return 'Шаблоны';
  } else if (drawerProps.value?.node?.type === 'simple') {
    return 'Редактирование шага';
  } else if (drawerProps.value?.node?.type === 'emitter') {
    return 'Редактирование эмиттера';
  } else if (drawerProps.value?.node?.type === 'template-instance') {
    return 'Редактирование шаблона';
  } else if (drawerProps.value?.botId && drawerRef.value?.$options?.__name === 'McpPrompt') {
    return 'MCP Builder';
  } else if (drawerProps.value?.botId) {
    return 'Редактирование бота';
  } else {
    return 'Редактирование';
  }
};
</script>

<template>
  <div
    v-click-outside="handleClickOutside"
    :class="isFullScreen ? 'full-screen' : ''"
    class="settings-drawer"
  >
    <div class="flex-div">
      <h3>{{ getDrawerTitle() }}</h3>
      <div class="buttons">
        <button
          v-if="drawerProps?.node?.type === 'emitter' || drawerProps?.node?.type === 'simple'"
          @click="deleteStep"
        >
          <TrashIcon class="icon" />
        </button>
        <button @click="isFullScreen = !isFullScreen">
          <FullScreenIcon />
        </button>
        <button @click="close">
          <CloseIcon />
        </button>
      </div>
    </div>
    <slot />
  </div>
</template>

<style scoped>
.settings-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 450px;
  height: 100%;
  border-left: 1px solid rgb(116, 116, 116);
  background: rgb(49, 49, 49);
  z-index: 999;
  padding: 15px;
  overflow: auto;
}

h3 {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

.flex-div {
  display: flex;
  justify-content: space-between;
}

.buttons {
  display: flex;
  gap: 10px;
}

.icon {
  width: 18px;
  height: auto;
  stroke: #ffffff;
}

.full-screen {
  width: calc(100% - v-bind(asideWidth));
}
</style>
