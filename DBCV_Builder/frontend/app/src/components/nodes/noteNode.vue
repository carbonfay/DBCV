<template>
  <div class="note-node" @mouseleave="hideToolbarWithDelay" @mouseover="showToolbarWithDelay">
    <div class="header-block">
      <nodeHeader style="margin-right: auto" title="Заметка" :showIcon="false"  />
      <button @click.stop="toggleEdit">
        <EditIcon v-if="!isEditing" class="icon" />
        <SaveIcon v-else class="icon" @click="emitUpdate" />
      </button>
      <ArrowIcon :class="['icon', { rotated: isExpanded }]" @click="toggleExpand" />
    </div>
    <div :class="['content-block', { 'change-color': isExpanded }]">
      <p v-if="!isEditing">
        {{ displayedContent }}
      </p>
      <textarea
        v-else
        ref="textarea"
        v-model="content"
        class="editable-textarea"
        @input="autoResize"
      ></textarea>
    </div>

    <NodeToolbar
      :is-visible="showToolbar"
      :position="Position.Top"
      @mouseleave="hideToolbarWithDelay"
      @mouseover="keepToolbarVisible"
    >
      <button @click="emitDelete">
        <TrashIcon class="icon trash-icon" />
      </button>
    </NodeToolbar>

    <Handle :position="Position.Left" type="source" />
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import nodeHeader from '@/components/nodes/nodeHeader.vue';
import { ArrowIcon, EditIcon, SaveIcon, TrashIcon } from '@/components/icons'; // импорт иконок

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['action']);

const content = ref(props.node.data.text || '');
const isExpanded = ref(false);
const isEditing = ref(false);
const textarea = ref(null);
const maxChars = 60;

const displayedContent = computed(() =>
  isExpanded.value || content.value.length <= maxChars
    ? content.value
    : `${content.value.slice(0, maxChars)}...`
);

const toggleExpand = () => (isExpanded.value = !isEditing.value && !isExpanded.value);

const toggleEdit = () => {
  isEditing.value = !isEditing.value;
  if (isEditing.value) {
    nextTick(autoResize);
  }
};

const autoResize = () => {
  const el = textarea.value;
  if (el) {
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
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

// Эмит для удаления
const emitDelete = () => {
  const isConfirmed = window.confirm('Вы уверены, что хотите удалить этот узел?');
  if (isConfirmed) {
    emit('action', { action: 'delete', data: { id: props.node.id, type: props.node.type } });
  }
};

// Эмит для обновления
const emitUpdate = () => {
  emit('action', {
    action: 'update',
    data: { id: props.node.id, type: props.node.type, text: content.value },
  });
};
</script>

<style scoped>
.note-node {
  padding: 0 15px 10px;
  border: 1px solid rgb(44, 59, 67);
  border-radius: 9px;
  width: 260px;
  background: rgba(44, 59, 67, 0.58);
}

.note-node:hover {
  background: rgba(44, 59, 67, 1);
}

.header-block {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 10px;
}

.content-block p {
  color: rgba(255, 255, 255, 0.44);
  font-size: 14px;
  font-weight: 500;
  line-height: 17px;
  letter-spacing: 0;
  margin-bottom: 10px;
  word-wrap: break-word;
}

.content-block.change-color p {
  color: rgba(255, 255, 255, 1);
}

.icon {
  width: 12px;
  height: auto;
  cursor: pointer;
  fill: rgb(255, 255, 255);
  transition: transform 0.3s ease-in-out;
}

.icon.rotated {
  transform: rotate(180deg);
}

textarea {
  border-radius: 3px;
  background: transparent;
  border: 0;
  color: #fff;
  padding: 10px 5px;
  width: 100%;
  font-size: 14px;
  font-weight: 500;
  line-height: 17px;
}

textarea::-webkit-scrollbar {
  width: 6px;
}

textarea::-webkit-scrollbar-track {
  background: rgb(243, 242, 231);
  border-radius: 10px;
}

textarea::-webkit-scrollbar-thumb {
  background: rgb(48, 68, 81);
  border-radius: 10px;
  transition: background-color 0.3s ease;
}

.icon.trash-icon {
  width: 18px;
  stroke: #ffffff;
  fill: none;
}
</style>
