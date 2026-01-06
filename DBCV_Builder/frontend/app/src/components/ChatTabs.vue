<template>
  <div class="chat-tabs-container" :class="{ expanded: isExpanded }">
    <div class="chat-tabs-header">
      <BasePanelTabs
        :tabs="channelTabs"
        :active-tab="activeChannelId"
        @tab-change="handleTabChange"
      />
      <div class="header-actions">
        <button @click="toggleExpand" class="expand-button">
          <i :class="isExpanded ? 'fas fa-compress' : 'fas fa-expand'"></i>
        </button>
        <button @click="closeChat" class="close-button">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="chat-content">
      <chatView v-if="activeChannel" :channel="activeChannel" :show-actions="false" />
      <div v-else class="no-channel-selected">
        <p>Выберите канал для общения</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import chatView from '@/components/chatView.vue';
import BasePanelTabs from './ui/BasePanelTabs.vue';

const props = defineProps({
  channels: {
    type: Array,
    required: true,
    default: () => [],
  },
});

const emit = defineEmits(['close']);

const activeChannelId = ref(null);
const isExpanded = ref(false);

if (props.channels.length > 0 && !activeChannelId.value) {
  activeChannelId.value = props.channels[0].id;
}

const channelTabs = computed(() => {
  return props.channels.map((channel) => ({
    name: channel.id,
    label: getChannelName(channel.name),
  }));
});

const activeChannel = computed(() => {
  return props.channels.find((channel) => channel.id === activeChannelId.value);
});

const getChannelName = (name) => {
  if (name.length > 15) {
    return name.substring(0, 12) + '...';
  }
  return name;
};

const handleTabChange = (currentTab, nextTab) => {
  activeChannelId.value = nextTab;
};

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};

const closeChat = () => {
  emit('close');
};
</script>

<style scoped>
.chat-tabs-container {
  position: fixed;
  right: 0;
  bottom: 0;
  width: 400px;
  height: 100vh;
  background: rgba(49, 49, 49, 1);
  border-left: 1px solid rgba(116, 116, 116, 1);
  border-top: 1px solid rgba(116, 116, 116, 1);
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.chat-tabs-container.expanded {
  width: 100vw;
  height: 100vh;
}

.chat-tabs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
  background: rgba(40, 40, 40, 1);
  border-bottom: 1px solid rgba(116, 116, 116, 1);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.expand-button,
.close-button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 5px;
  font-size: 14px;
}

.expand-button:hover,
.close-button:hover {
  color: #ccc;
}

.chat-content {
  flex: 1;
  overflow: hidden;
}

.no-channel-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #fff;
}
</style>
