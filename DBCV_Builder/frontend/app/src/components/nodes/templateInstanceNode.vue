<template>
  <div
    class="template-instance-node"
    @click="openSettings"
    @mouseleave="hideToolbarWithDelay"
    @mouseover="showToolbarWithDelay"
  >
    <nodeHeader :title="node.data.name || 'Template Instance'" :showIcon="false" />
    <div class="template-info">
      <div class="template-badge">
        <span class="template-label">Template</span>
        <span class="template-id">{{ node.data.template_id }}</span>
      </div>
    </div>
    <NodeToolbar
      :is-visible="showToolbar"
      :position="Position.Top"
      @mouseleave="hideToolbarWithDelay"
      @mouseover="keepToolbarVisible"
    >
      <button @click="handleAction('delete')">
        <TrashIcon class="icon" />
      </button>
      <button @click="openSettings">
        <Edit2Icon class="icon edit-icon" />
      </button>
    </NodeToolbar>

    <Handle :position="Position.Left" type="target" />
    <Handle :position="Position.Right" type="source" />
  </div>
</template>

<script setup>
import { inject, ref } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import { Edit2Icon, TrashIcon } from '@/components/icons';
import nodeHeader from '@/components/nodes/nodeHeader.vue';
import TemplateInstancePanel from '@/components/panels/templateInstancePanel.vue';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['action']);
const handleAction = (action) => {
  if (action === 'delete') {
    const isConfirmed = window.confirm('Вы уверены, что хотите удалить этот template instance?');
    if (isConfirmed) {
      emit('action', { action: 'delete', data: { id: props.node.id, type: props.node.type } });
    }
  }
};

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

const { setDrawer, setProps } = inject('drawer');

const openSettings = () => {
  setDrawer(TemplateInstancePanel);
  setProps({ node: props.node });
};
</script>

<style scoped>
.template-instance-node {
  border: 2px solid rgb(255, 193, 7);
  border-radius: 9px;
  box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.15);
  padding: 0 15px;
  width: 280px;
  background: rgb(29, 76, 99);
  transition: opacity 0.3s ease-in-out;
  position: relative;
  opacity: 0.9;
}

.template-instance-node:hover {
  opacity: 1;
}

.template-instance-node::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-top: 20px solid rgba(255, 193, 7, 1);
  border-top-right-radius: 9px;
}

.template-info {
  margin: 10px 0;
}

.template-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgb(44, 55, 64);
  border-radius: 4px;
  padding: 4px 8px;
}

.template-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 193, 7);
}

.template-id {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 3px;
}

.variables-preview {
  margin: 10px 0;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.variables-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 193, 7);
  display: block;
  margin-bottom: 4px;
}

.variables-json {
  font-size: 9px;
  font-family: monospace;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 60px;
  overflow: hidden;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
}

.status-indicator.active .status-dot {
  background: #4caf50;
}

.status-text {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
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

.template-instance-node.removing {
  opacity: 0;
}
</style>
