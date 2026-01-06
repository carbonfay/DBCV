<template>
  <div
    class="emitter-node"
    @click="openSettings"
    @mouseover="showToolbarWithDelay"
    @mouseleave="hideToolbarWithDelay"
  >
    <nodeHeader :showIcon="false" :title="props.node.data.name || 'Эмиттер'" />
    <span class="desc" v-if="props.node.data.cron?.name">
      {{ props.node.data.cron_name || props.node.data.cron.name }}
    </span>

    <button
      class="control-panel"
      :disabled="!props.node.data.cron_id || !props.node.data.message_id"
      :title="(!props.node.data.cron_id || !props.node.data.message_id) ? getDisabledReason() : ''"
      @click="toggleActiveState"
    >
      <StopIcon v-if="isActive" class="icon" />
      <PlayIcon v-else class="icon play-icon" />
      {{ isActive ? 'стоп' : 'пуск' }}
    </button>

    <NodeToolbar
      :is-visible="showToolbar"
      :position="Position.Top"
      @mouseover="keepToolbarVisible"
      @mouseleave="hideToolbarWithDelay"
    >
      <button @click="handleAction('delete')">
        <TrashIcon class="icon" />
      </button>
      <button @click="handleAction('copy')">
        <CopyIcon class="icon" />
      </button>
      <button @click="openSettings">
        <Edit2Icon class="icon edit-icon" />
      </button>
    </NodeToolbar>
  </div>
</template>

<script setup>
import { inject, onUpdated, ref } from 'vue';
import { Position } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import { CopyIcon, Edit2Icon, PlayIcon, StopIcon, TrashIcon } from '@/components/icons'; // импорт иконок
import notyf from '@/plugins/notyf';
import nodeHeader from '@/components/nodes/nodeHeader.vue';
import EmitterNodePanel from '@/components/panels/emitterNodePanel.vue';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const isActive = ref(props.node.data.is_active);

// Определяем причину блокировки кнопки
const getDisabledReason = () => {
  const hasCron = props.node.data.cron_id;
  const hasMessage = props.node.data.message_id;
  
  if (!hasCron && !hasMessage) {
    return 'Укажите частоту запуска и сообщение';
  } else if (!hasCron) {
    return 'Укажите частоту запуска';
  } else if (!hasMessage) {
    return 'Укажите сообщение';
  }
  return '';
};

const emit = defineEmits(['action']);
const handleAction = (action) => {
  if (action === 'delete') {
    const isConfirmed = window.confirm('Вы уверены, что хотите удалить этот узел?');
    if (isConfirmed) {
      emit('action', { action: 'delete', data: { id: props.node.id, type: props.node.type } });
    }
  } else if (action === 'copy') {
    emit('action', { action: 'copy', data: { id: props.node.id, type: props.node.type } });
  }
};

// Появление меню блока при наведении
const showToolbar = ref(false);
let hideTimeout = null;

const showToolbarWithDelay = () => {
  clearTimeout(hideTimeout);
  showToolbar.value = true;
};

const hideToolbarWithDelay = () => {
  hideTimeout = setTimeout(() => {
    showToolbar.value = false;
  }, 300);
};

const keepToolbarVisible = () => {
  clearTimeout(hideTimeout);
};

const toggleActiveState = () => {
  isActive.value = !isActive.value;
  notyf.success(isActive.value ? 'Запущено!' : 'Остановлено!');
  const updatedNode = {
    is_active: isActive.value,
    type: 'emitter',
    id: props.node.id,
  };

  emit('action', { action: 'update', data: updatedNode });
  if (drawerProps.value?.node?.id === props.node.id) {
    setProps({
      node: { ...props.node, data: { ...props.node.data, is_active: isActive.value } },
    });
  }
};

const { setDrawer, setProps, drawerProps } = inject('drawer');

const openSettings = () => {
  setDrawer(EmitterNodePanel);
  setProps({ node: props.node });
};
</script>

<style scoped>
.emitter-node {
  border: 1px solid rgb(51, 64, 71);
  border-radius: 9px;
  box-shadow: 0px 2px 2px 0px rgba(0, 0, 0, 0.15);
  background: rgb(44, 55, 64);
  width: 250px;
  padding: 0 15px;
  opacity: 0.9;
  transition: opacity 0.3s ease-in-out;
}

.emitter-node:hover {
  opacity: 1;
}

span.desc {
  display: block;
  border-radius: 3px;
  background: rgb(243, 242, 231);
  width: 100%;
  color: #373737;
  padding: 15px;
  text-align: left;
  overflow: hidden;
  margin-top: 10px;
}

.icon {
  width: 18px;
  height: auto;
  stroke: #ffffff;
}

.icon.edit-icon {
  fill: #ffffff;
  stroke: none;
  width: 20px;
}

.icon.play-icon {
  width: 12px;
}

.control-panel {
  display: block;
  margin: 13px auto 26px;
  border-radius: 6px;
  background: rgb(188, 46, 72);
  padding: 14px;
  display: flex;
  gap: 10px;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 12px;
  align-items: center;
  max-height: 44px;
}

.control-panel:disabled {
  background-color: rgb(167 104 115);
  cursor: not-allowed;
}
</style>
