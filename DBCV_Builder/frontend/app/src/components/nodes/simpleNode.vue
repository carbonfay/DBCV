<template>
  <div
    class="simple-node"
    :style="nodeStyle"
    @click="openSettings"
    @mouseleave="hideToolbarWithDelay"
    @mouseover="showToolbarWithDelay"
  >
    <nodeHeader :title="node.data.name || 'Название шага'" :show-icon="false">
      <template v-if="integrationIcon" #icon>
        <img :src="integrationIcon" :alt="integrationName" class="integration-icon-img" />
      </template>
    </nodeHeader>
    <span v-if="node.data.message && node.data.message.text" class="desc">
      {{ truncateText(node.data.message.text) }}
    </span>
    <nodeFooter :node="node" />

    <NodeToolbar
      :is-visible="showToolbar"
      :position="Position.Top"
      @mouseleave="hideToolbarWithDelay"
      @mouseover="keepToolbarVisible"
    >
      <button @click.stop="handleAction('delete')">
        <TrashIcon class="icon" />
      </button>
      <button @click.stop="handleAction('copy')">
        <CopyIcon class="icon" />
      </button>
      <button @click.stop="openExecuteModal">
        <PlayIcon class="icon" />
      </button>
      <button @click.stop="openSettings">
        <Edit2Icon class="icon edit-icon" />
      </button>
    </NodeToolbar>

    <Handle :position="Position.Left" type="target" />
    <Handle :position="Position.Right" type="source" />

    <StepExecuteModal 
      v-if="showExecuteModal"
      :step="{ ...node.data, id: node.id }"
      @close="closeExecuteModal"
    />
  </div>
</template>

<script setup lang="ts">
import { inject, ref, computed, onMounted } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import { CopyIcon, Edit2Icon, TrashIcon, PlayIcon } from '@/components/icons'; // импорт иконок
import nodeHeader from '@/components/nodes/nodeHeader.vue';
import nodeFooter from '@/components/nodes/nodeFooter.vue';
import SimpleNodePanel from '@/components/panels/simpleNodePanel.vue';
import StepExecuteModal from '@/components/modals/stepExecuteModal.vue';
import integrationsApi from '@/api/services/integrationsApi';

const props = defineProps<{
  node: any;
}>();

const emit = defineEmits<{
  (e: 'action', payload: { action: string; data: any }): void;
}>();

const handleAction = (action: string) => {
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
const showExecuteModal = ref(false);
let hideTimeout: ReturnType<typeof setTimeout> | null = null;

const showToolbarWithDelay = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
  showToolbar.value = true;
};

const hideToolbarWithDelay = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
  hideTimeout = setTimeout(() => {
    showToolbar.value = false;
  }, 300);
};

const keepToolbarVisible = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
};

const drawer = inject<{ setDrawer: (component: any) => void; setProps: (props: any) => void }>('drawer');
const setDrawer = drawer?.setDrawer;
const setProps = drawer?.setProps;

const openSettings = () => {
  if (setDrawer && setProps) {
    setDrawer(SimpleNodePanel);
    setProps({ node: props.node });
  }
};

const openExecuteModal = () => {
  showExecuteModal.value = true;
};

const closeExecuteModal = () => {
  showExecuteModal.value = false;
};

const truncateText = (text: string) => {
  if (!text) return '';
  if (text.length <= 80) return text;
  return text.substring(0, 80) + '...';
};

// Интеграции
const integrationMetadata = ref<any>(null);
const integrationIcon = computed(() => integrationMetadata.value?.icon_url || null);
const integrationName = computed(() => integrationMetadata.value?.name || '');
const integrationColor = computed(() => integrationMetadata.value?.color || null);

const nodeStyle = computed(() => {
  if (integrationColor.value) {
    return {
      borderLeftColor: integrationColor.value,
      borderLeftWidth: '4px',
      borderLeftStyle: 'solid' as const,
    };
  }
  return {};
});

// Загружаем метаданные интеграции если есть
onMounted(async () => {
  const connectionGroups = props.node.data?.connection_groups || [];
  const integrationGroup = connectionGroups.find(
    (group: any) => group.search_type === 'integration' && group.integration_id
  );
  
  if (integrationGroup?.integration_id) {
    try {
      const response = await integrationsApi.getMetadata(integrationGroup.integration_id);
      if (response?.data) {
        integrationMetadata.value = response.data;
      }
    } catch (error) {
      console.error('Error loading integration metadata for node:', error);
    }
  }
});
</script>

<style scoped>
.simple-node {
  border:
    2px solid rgb(0, 145, 255),
    rgb(51, 64, 71);
  border-radius: 9px;
  box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.15);
  padding: 0 15px;
  width: 250px;
  background: rgb(29, 76, 99);
  opacity: 0.9;
  transition: opacity 0.3s ease-in-out;
}

.simple-node:hover {
  opacity: 1;
  background: rgb(29 77 101);
}

/* .simple-node::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-top: 20px solid rgba(255, 187, 40, 1);
  border-top-right-radius: 9px;
} */

.simple-node.removing {
  opacity: 0;
}

h3 {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

span {
  font-size: 16px;
  color: #373737;
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
  line-height: 1.275;
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

.integration-icon-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
  margin-right: 8px;
}
</style>
