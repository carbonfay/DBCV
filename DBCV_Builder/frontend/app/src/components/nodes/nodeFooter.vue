<template>
  <div class="footer">
    <button class="card repeat" style="margin-right: auto" @click="openLogTab">
      <RepeatIcon class="icon" />
      <span>0</span>
    </button>
    <button v-if="errors > 0" class="card" @click="openLogTab">
      <ErrorIcon class="icon" />
      <span>{{ errors }}</span>
    </button>
    <button v-if="pythonCalls > 0" class="card" @click="openConnectionsTab">
      <PythonIcon class="icon" />
      <span>{{ pythonCalls }}</span>
    </button>
    <button v-if="apiCalls > 0" class="card api" @click="openConnectionsTab">
      <span style="margin: 0">API</span>
      <span>{{ apiCalls }}</span>
    </button>
    <button class="card" @click="openConnectionsTab">
      <ConnectionIcon class="icon" />
      <span>{{ connectionsCount }}</span>
    </button>
    <button class="card hidden">
      <ClipIcon class="icon" />
    </button>
  </div>
</template>

<script setup>
import { ClipIcon, ConnectionIcon, ErrorIcon, PythonIcon, RepeatIcon } from '@/components/icons';
import { inject } from 'vue';
import SimpleNodePanel from '@/components/panels/simpleNodePanel.vue'; // импорт иконок

const { node } = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const connectionGroups = node.data.connection_groups ?? [];
const connectionGroupsTypes = connectionGroups.map((group) => group.search_type);

const errors = 0;

const pythonCalls = connectionGroupsTypes.filter((type) => type === 'code').length;
const apiCalls = connectionGroupsTypes.filter((type) => type === 'response').length;
const connectionsCount = connectionGroups.flatMap(
  (connectionGroup) => connectionGroup.connections
).length;

const { setDrawer, setProps } = inject('drawer');

const openSettings = async (tab) => {
  setProps({ node, initActiveTab: tab });
  await setDrawer(SimpleNodePanel);
};

const openConnectionsTab = async () => {
  await openSettings('connections');
};

const openLogTab = async () => {
  await openSettings('log');
};
</script>

<style scoped>
.footer {
  padding: 5px 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.icon {
  height: auto;
  width: 11px;
}

.card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 5px;
  width: auto !important;
}

.card.repeat {
  cursor: auto;
}

.card span {
  font-size: 11px;
  font-weight: 700;
  line-height: 12px;
  margin-left: 4px;
}

.card.api span {
  color: #ffbb28;
}

.card.repeat span {
  opacity: 0.58;
}

.card:hover {
  border-radius: 3px;
  background: rgba(29, 58, 70, 0.8);
}

.card:active {
  border-radius: 3px;
  background: rgba(29, 58, 70, 1);
}

/*.card.repeat:hover,
.card.repeat:active {
  background: transparent;
}*/

.hidden {
  display: none;
}
</style>
