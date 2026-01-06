<template>
  <div style="display: flex; width: 100vw; height: 100vh">
    <asidePanel ref="aside" :botId="botId" :botInfo="botInfo" :nodes="nodes" />
    <buttonsPanel
      :templateGroupsInfo="templateGroupsInfo"
      :bot-id="botId"
      @add-node="addNode"
      @select-template-group="handleGroupSelect"
    />
    <variableViewer v-if="botVariables" :botId="botId" />
    <div style="flex: 1; display: flex; flex-direction: column">
      <VueFlow
        :edges="edges"
        :nodes="nodes"
        class="transition-flow"
        @connect="onConnect"
        @drop="onDrop"
        @dragover.prevent
      >
        <Background gap="40" patternColor="rgba(255, 255, 255, 0.03)" variant="lines" />
        <template #node-simple="props">
          <simpleNode v-if="nodeIsVisible[props.id]" :node="props" @action="handleAction" />
        </template>
        <template #node-emitter="props">
          <emitterNode v-if="nodeIsVisible[props.id]" :node="props" @action="handleAction" />
        </template>
        <template #node-note="props">
          <noteNode :node="props" @action="handleAction" />
        </template>
        <template #node-template-instance="props">
          <templateInstanceNode
            v-if="nodeIsVisible[props.id]"
            :node="props"
            @action="handleAction"
          />
        </template>
        <template #edge-custom="props">
          <CustomEdge :ref="(c) => (edgeRefs[props.id] = c)" v-bind="props" />
        </template>
      </VueFlow>
    </div>
    <button
      v-if="hasChannels"
      @click="toggleChat"
      class="chat-toggle-button"
      :class="{ active: showChat }"
    >
      <i class="fas fa-comment"></i>
    </button>
    <ControlPanel v-if="drawerComponent" :aside-width="aside?.width" @action="handleAction">
      <Component :is="drawerComponent" ref="drawer" v-bind="drawerProps" @action="handleAction" />
    </ControlPanel>
    <templateInstanceModal
      v-if="showTemplateInstanceModal && templateToInstance"
      :template="templateToInstance"
      :botId="botId"
      @close="closeTemplateInstanceModal"
      @save="saveTemplateInstance"
    />
    <ChatTabs
      v-if="showChat && hasChannels"
      :channels="botInfo?.channels || []"
      @close="closeChat"
    />
  </div>
</template>

<script setup>
import {
  nextTick,
  onBeforeUnmount,
  onMounted,
  provide,
  reactive,
  ref,
  shallowRef,
  useTemplateRef,
  computed,
} from 'vue';
import { MarkerType, useVueFlow, VueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import simpleNode from '@/components/nodes/simpleNode.vue';
import emitterNode from '@/components/nodes/emitterNode.vue';
import noteNode from '@/components/nodes/noteNode.vue';
import templateInstanceNode from '@/components/nodes/templateInstanceNode.vue';
import asidePanel from '@/components/asidePanel.vue';
import variableViewer from '@/components/variableViewer.vue';
import buttonsPanel from '@/components/buttonsPanel.vue';
import ChatTabs from '@/components/ChatTabs.vue';
import TemplatesModal from '@/components/TemplatesModal.vue';
import { useRoute } from 'vue-router';
import {
  useBotsStore,
  useConnectionGroupsStore,
  useEmittersStore,
  useNotesStore,
  useStepsStore,
  useWebsocketBotStore,
  useTemplatesInstanceStore,
  useAuthStore,
  useTemplateGroupsStore,
} from '@/stores';
import ControlPanel from '@/components/controlPanel.vue';
import CustomEdge from '@/components/edges/customEdge.vue';
import templateInstanceModal from '@/components/modals/templateInstanceModal.vue';
import { useCameraPosition } from '@/composables';
import SimpleNodePanel from '@/components/panels/simpleNodePanel.vue';
import EmitterNodePanel from '@/components/panels/emitterNodePanel.vue';

const aside = useTemplateRef('aside');

const {
  updateNodeData,
  removeNodes,
  removeEdges,
  onNodeDragStop,
  addNodes,
  addEdges,
  updateNode,
  updateNodeInternals,
  setCenter,
  viewport,
  screenToFlowCoordinate,
} = useVueFlow();

const edgeRefs = reactive({});

const nodes = ref([]);
const edges = ref([]);

const route = useRoute();
const botStore = useBotsStore();
const stepStore = useStepsStore();
const connectionGroupsStore = useConnectionGroupsStore();
const noteStore = useNotesStore();
const emittersStore = useEmittersStore();
const websocketStore = useWebsocketBotStore();
const templatesInstanceStore = useTemplatesInstanceStore();
const authStore = useAuthStore();
const templateGroupsStore = useTemplateGroupsStore();
const botId = route.params.id;
botStore.botId = botId;

const drawerComponent = shallowRef(null);
const drawerProps = ref(null);
const drawerRef = useTemplateRef('drawer');

const showChat = ref(false);

// Инициализируем работу с камерой
const { initCameraTracking, setupViewportTracking, saveCameraPosition } = useCameraPosition(botId);

// Функция очистки отслеживания viewport
const cleanupViewportTracking = ref(null);

const setDrawer = async (value) => {
  if (drawerRef.value && typeof drawerRef.value.save === 'function') drawerRef.value?.save();
  drawerComponent.value = null;
  await nextTick();
  drawerComponent.value = value;
  if (
    ['simpleNodePanel', 'emitterNodePanel', 'templateInstancePanel'].includes(value?.__name) &&
    drawerProps.value?.node?.id
  ) {
    nextTick(() => {
      centerOnNode(drawerProps.value.node.id);
    });
  }
};

const centerOnNode = (nodeId) => {
  const node = nodes.value.find((n) => n.id === nodeId);
  if (node) {
    const nodePosition = node.position;
    const currentZoom = viewport.value.zoom;
    const isDrawerOpen = drawerComponent.value !== null;
    const baseOffset = isDrawerOpen ? 225 : 125;
    const offsetX = baseOffset / currentZoom;
    
    setCenter(nodePosition.x + offsetX, nodePosition.y + 50, {
      duration: 500,
      zoom: currentZoom,
    });
  }
};
const setProps = (props) => (drawerProps.value = props);
provide('drawer', {
  drawerComponent,
  drawerProps,
  drawerRef,
  setDrawer,
  setProps,
});

const nodeIsVisible = reactive({});
const token = authStore.accessToken;

const showTemplateInstanceModal = ref(false);
const templateToInstance = ref(null);
const dropPosition = ref({ x: 0, y: 0 });

// Получение данных о боте
const mapStepsToNodes = (steps) =>
  steps.map((step) => {
    if (step.template_instance) {
      return {
        id: step.id,
        position: { x: step.pos_x, y: step.pos_y },
        data: {
          name: step.name,
          description: step.description || '',
          is_proxy: step.is_proxy,
          connection_groups: step.connection_groups,
          message: step.message,
          template_id: step.template_instance.id,
          template_name: step.template_instance.name,
          variables: step.template_instance.variables,
          inputs_mapping: step.template_instance.inputs_mapping,
          outputs_mapping: step.template_instance.outputs_mapping,
          template_instance: step.template_instance,
        },
        type: 'template-instance',
      };
    } else {
      return {
        id: step.id,
        position: { x: step.pos_x, y: step.pos_y },
        data: {
          name: step.name,
          description: step.description || '',
          is_proxy: step.is_proxy,
          connection_groups: step.connection_groups,
          message: step.message,
        },
        type: 'simple',
      };
    }
  });

const mapNotesToNodes = (notes) =>
  notes.map((note) => ({
    id: note.id,
    position: { x: note.pos_x, y: note.pos_y },
    data: {
      text: note.text || '',
    },
    type: 'note',
  }));

const mapEmittersToNodes = (emitters) =>
  emitters.map((emitter) => ({
    id: emitter.id,
    position: { x: emitter.pos_x, y: emitter.pos_y },
    data: {
      name: emitter.name,
      is_active: emitter.is_active,
      message_id: emitter.message_id,
      cron_id: emitter.cron_id,
      cron: emitter.cron,
      message: emitter.message,
      needs_message_processing: emitter.needs_message_processing,
    },
    type: 'emitter',
  }));

const mapConnectionsToEdges = (steps) =>
  steps.flatMap((step) =>
    step.connection_groups.flatMap((group) =>
      group.connections.map((connection) => ({
        id: `e${step.id}-${connection.next_step_id}`,
        source: step.id,
        target: connection.next_step_id,
        type: 'custom',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'rgb(207, 255, 125)',
        },
      }))
    )
  );

const mapNoteConnectionsToEdges = (notes) =>
  notes
    .filter((note) => note.step_id)
    .map((note) => ({
      id: `e${note.step_id}-${note.id}`,
      source: note.step_id,
      target: note.id,
      type: 'custom',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: 'rgb(207, 255, 125)',
      },
    }));

const fetchBotData = async () => {
  const response = await botStore.readBot(botId);
  const botInfo = response?.data;
  console.log(botInfo);

  if (!botInfo) {
    console.error('Не удалось получить данные агента');
    return null;
  }

  const stepNodes = mapStepsToNodes(botInfo.steps);
  const noteNodes = mapNotesToNodes(botInfo.notes);
  const emitterNodes = mapEmittersToNodes(botInfo.emitters);

  nodes.value = [...stepNodes, ...noteNodes, ...emitterNodes];
  nodes.value.forEach((node) => showNode(node.id));
  await nextTick();
  edges.value = [
    ...mapConnectionsToEdges(botInfo.steps),
    ...mapNoteConnectionsToEdges(botInfo.notes),
  ];

  console.log('Узлы:', nodes.value);
  console.log('Связи:', edges.value);
  return botInfo;
};

// Добавление нового узла
const getCenterPosition = () => {
  const screenCenterX = (window.innerWidth || 800) / 2;
  const screenCenterY = (window.innerHeight || 600) / 2;
  
  const flowPosition = screenToFlowCoordinate({ x: screenCenterX, y: screenCenterY });
  
  return { x: flowPosition.x, y: flowPosition.y };
};

const addNode = async ({ type, name }) => {
  let id = null;
  if (type === 'simple') {
    const response = await stepStore.createStep({
      name: name,
      is_proxy: false,
      bot_id: botId,
      description: '',
      pos_x: getCenterPosition().x,
      pos_y: getCenterPosition().y,
    });

    addNodes({
      id: response.id,
      position: { x: response.pos_x, y: response.pos_y },
      data: {
        name: name,
        description: '',
        is_proxy: false,
        connection_groups: response.connection_groups,
        message: response.message,
      },
      type: 'simple',
    });
    id = response.id;
  } else if (type === 'emitter') {
    const response = await emittersStore.createEmitter({
      cron_id: '9e835989-f459-41aa-bb93-159083b0637f',
      pos_x: getCenterPosition().x,
      pos_y: getCenterPosition().y,
      name: name,
      is_active: false,
      bot_id: botId,
      needs_message_processing: false,
    });
    addNodes({
      id: response.id,
      position: { x: response.pos_x, y: response.pos_y },
      data: {
        name: response.name,
        is_active: response.is_active,
        needs_message_processing: response.needs_message_processing,
      },
      type: 'emitter',
    });
    id = response.id;
  } else if (type === 'note') {
    const response = await noteStore.createNote({
      text: '',
      bot_id: botId,
      step_id: null,
      pos_x: getCenterPosition().x,
      pos_y: getCenterPosition().y,
    });
    addNodes({
      id: response.id,
      position: { x: response.pos_x, y: response.pos_y },
      data: {
        text: response.text,
      },
      type: 'note',
    });
    id = response.id;
  } else {
    throw new Error(`Неизвестный тип узла: ${type}`);
  }
  showNode(id);
  await fetchBotData();
  
  // Автоматически открываем панель редактирования для созданного узла
  await nextTick();
  const createdNode = nodes.value.find(node => node.id === id);
  if (createdNode) {
    if (type === 'simple') {
      setDrawer(SimpleNodePanel);
      setProps({ node: createdNode });
    } else if (type === 'emitter') {
      setDrawer(EmitterNodePanel);
      setProps({ node: createdNode });
    }
  }
};

const refreshNode = async (id) => {
  nodeIsVisible[id] = false;
  await nextTick();
  nodeIsVisible[id] = true;
  await nextTick();
  updateNodeInternals([id]);
};

const showNode = (id) => {
  nodeIsVisible[id] = true;
};

// Обновление узла
const handleAction = async ({ action, data }) => {
  if (action === 'masterUpdate') {
    botInfo.value = data;
    setProps({ botInfo, botId });
  } else if (action === 'update') {
    if (data.type === 'simple') {
      const updatedData = Object.keys(data).reduce((acc, key) => {
        if (data[key] !== undefined) {
          acc[key] = data[key];
        }
        return acc;
      }, {});

      updateNodeData(data.id, updatedData);
      await stepStore.updateStep(data.id, updatedData);
    } else if (data.type === 'template-instance') {
      if (data.variables !== undefined) {
        const currentNode = nodes.value.find((node) => node.id === data.id);
        const templateInstanceData = {
          name: data.name || currentNode?.data?.name || '',
          description: data.description || currentNode?.data?.description || '',
          variables: data.variables,
        };
        await templatesInstanceStore.updateTemplateInstance(
          data.template_instance_id,
          templateInstanceData
        );
      } else {
        const updatedData = Object.keys(data).reduce((acc, key) => {
          if (data[key] !== undefined) {
            acc[key] = data[key];
          }
          return acc;
        }, {});

        updateNodeData(data.id, updatedData);
        await stepStore.updateStep(data.id, updatedData);
      }
    } else if (data.type === 'note') {
      const noteUpdateData = { text: data.text };
      await noteStore.updateNote(data.id, noteUpdateData);
    } else if (data.type === 'emitter') {
      const updatedData = Object.keys(data).reduce((acc, key) => {
        if (data[key] !== undefined) {
          acc[key] = data[key];
        }
        return acc;
      }, {});
      updateNodeData(data.id, updatedData);
      await emittersStore.updateEmitter(data.id, updatedData);
    }
    await fetchBotData();
    await refreshNode(data.id);
  } else if (action === 'graphUpdate') {
    if (data.type === 'simple') {
    } else if (data.type === 'template-instance') {
    } else if (data.type === 'note') {
      const noteUpdateData = { text: data.text };
      await noteStore.updateNote(data.id, noteUpdateData);
    } else if (data.type === 'emitter') {
      const noteUpdateData = {
        name: data.name,
        cron_id: data.cron_id,
        is_active: data.is_active,
        needs_message_processing: data.needs_message_processing,
        cron: { name: data.cron_name },
      };
      updateNodeData(data.id, noteUpdateData);
      await emittersStore.updateEmitter(data.id, noteUpdateData);
    }
    await fetchBotData();
    await refreshNode(data.id);
  } else if (action === 'delete') {
    removeNodes([data.id]);
    nodeIsVisible[data.id] = undefined;
    if (drawerProps.value?.node?.id === data.id) void setDrawer(null);

    if (data.type === 'simple') {
      await stepStore.deleteStep(data.id);
    } else if (data.type === 'template-instance') {
      await stepStore.deleteStep(data.id);
    } else if (data.type === 'note') {
      await noteStore.deleteNote(data.id);
    } else if (data.type === 'emitter') {
      await emittersStore.deleteEmitter(data.id);
    }

    const connectedEdges = edges.value.filter(
      (edge) => edge.source === data.id || edge.target === data.id
    );
    const edgeIds = connectedEdges.map((edge) => edge.id);
    removeEdges(edgeIds);

    await fetchBotData();
    const connectedNodes = new Set(
      connectedEdges
        .flatMap((edge) => [edge.source, edge.target])
        .filter((edge) => edge !== data.id)
    );
    for (const id of connectedNodes) {
      await refreshNode(id);
    }
  } else if (action === 'copy') {
    showNode(await copyNode(data.id));
  }
};

// Обновление при перемещении
onNodeDragStop(async (event) => {
  const { id, position, type } = event.node;
  if (type === 'simple') {
    await stepStore.updateStep(id, {
      pos_x: position.x,
      pos_y: position.y,
    });
  } else if (type === 'template-instance') {
    await stepStore.updateStep(id, {
      pos_x: position.x,
      pos_y: position.y,
    });
  } else if (type === 'note') {
    await noteStore.updateNote(id, {
      pos_x: position.x,
      pos_y: position.y,
    });
  } else if (type === 'emitter') {
    await emittersStore.updateEmitter(id, {
      pos_x: position.x,
      pos_y: position.y,
    });
  }
});

// Копирование узла
const copyNode = async (nodeId) => {
  const originalNode = nodes.value.find((node) => node.id === nodeId);
  if (!originalNode) {
    console.error('Узел не найден');
    return;
  }

  let id = null;
  if (originalNode.type === 'simple') {
    const response = await stepStore.createStep({
      name: originalNode.data.name + ' copy',
      is_proxy: originalNode.data.is_proxy,
      bot_id: botId,
      description: originalNode.data.description,
      pos_x: originalNode.position.x + 50,
      pos_y: originalNode.position.y + 50,
    });

    addNodes({
      id: response.id,
      position: { x: response.pos_x, y: response.pos_y },
      data: {
        name: response.name,
        description: response.description,
        is_proxy: response.is_proxy,
        message: response.message,
      },
      type: originalNode.type,
    });
    id = response.id;
  } else if (originalNode.type === 'emitter') {
    const response = await emittersStore.createEmitter({
      name: originalNode.data.name + ' copy',
      is_active: false,
      bot_id: botId,
      pos_x: originalNode.position.x + 50,
      pos_y: originalNode.position.y + 50,
      cron_id: originalNode.data.cron_id,
      message_id: originalNode.data.message_id,
      needs_message_processing: originalNode.data.needs_message_processing,
    });

    addNodes({
      id: response.id,
      position: { x: response.pos_x, y: response.pos_y },
      data: {
        name: response.name,
        is_active: response.is_active,
        cron_id: response.cron_id,
        message_id: response.message_id,
      },
      type: originalNode.type,
    });
    id = response.id;
  }
  return id;
};

// Обработка создания связи
const onConnect = async (connection) => {
  const sourceNode = nodes.value.find((node) => node.id === connection.source);
  const targetNode = nodes.value.find((node) => node.id === connection.target);

  if (!sourceNode || !targetNode) {
    console.error('Исходный или целевой узел не найден');
    return;
  }

  let validSource = sourceNode;
  let validTarget = targetNode;

  if (sourceNode.type === 'note') {
    [validSource, validTarget] = [targetNode, sourceNode];
  }

  addEdges([
    {
      id: `e${validSource.id}-${validTarget.id}`,
      source: validSource.id,
      target: validTarget.id,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: 'rgb(207, 255, 125)',
      },
    },
  ]);

  if (validTarget.type === 'simple') {
    const newGroupData = {
      search_type: 'message',
      priority: 0,
      step_id: validSource.id,
      code: null,
      request_id: null,
      variables: null,
      connections: [
        {
          next_step_id: validTarget.id,
          rules: null,
          priority: 0,
          filters: null,
        },
      ],
    };
    await connectionGroupsStore.createConnectionGroup(newGroupData);
    await fetchBotData();
    refreshNode(validSource.id);
  } else if (validTarget.type === 'note') {
    await noteStore.updateNote(validTarget.id, {
      step_id: validSource.id,
    });
  }
};

const selectedGroup = ref(null);

const handleGroupSelect = async (group) => {
  selectedGroup.value = group;
  setProps({
    group: selectedGroup.value,
    botId: botId,
    show: true,
    nodes: nodes.value,
  });
  await setDrawer(TemplatesModal);
};

const closeTemplatesModal = () => {
  setDrawer(null);
  selectedGroup.value = null;
};

const handleTemplateSelect = (template) => {
  templateToInstance.value = template;
  showTemplateInstanceModal.value = true;
  closeTemplatesModal();
};

provide('nodes', nodes);
provide('edges', edges);

// Функция для обновления данных бота (для MCP компонента)
const refreshBotData = async () => {
  const botResponse = await fetchBotData();
  botInfo.value = botResponse;
  
  if (botResponse && botResponse.variables) {
    botVariables.value = botResponse.variables.data;
  }
};

provide('refreshBotData', refreshBotData);

const botInfo = ref(null);
const botVariables = ref(null);
const templateGroupsInfo = ref(null);

onMounted(async () => {
  const botResponse = await fetchBotData();
  botInfo.value = botResponse;

  const templateGroupsResponse = await templateGroupsStore.readTemplateGroups();
  templateGroupsInfo.value = templateGroupsResponse.data;

  if (botResponse && botResponse.variables) {
    botVariables.value = botResponse.variables.data;
  }

  await nextTick();
  initCameraTracking();
  cleanupViewportTracking.value = setupViewportTracking();

  websocketStore.connect(botId, token, botVariables.value);
});

onBeforeUnmount(() => {
  saveCameraPosition();
  
  if (cleanupViewportTracking.value) {
    cleanupViewportTracking.value();
  }
  websocketStore.disconnect(botId);
});

function onDrop(event) {
  try {
    const data = JSON.parse(event.dataTransfer.getData('application/json'));
    if (data.type === 'template') {
      const rect = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      dropPosition.value = position;
      templateToInstance.value = data.template;
      showTemplateInstanceModal.value = true;
      closeTemplatesModal();
    }
  } catch (error) {
    console.error('Ошибка при обработке drop:', error);
  }
}

function closeTemplateInstanceModal() {
  showTemplateInstanceModal.value = false;
  templateToInstance.value = null;
}

async function saveTemplateInstance(data) {
  try {
    const response = await templatesInstanceStore.createTemplateInstance({
      ...data,
      pos_x: dropPosition.value.x,
      pos_y: dropPosition.value.y,
    });

    if (response && response.steps) {
      const stepNodes = response.steps.map((step) => ({
        id: step.id,
        position: { x: step.pos_x, y: step.pos_y },
        data: {
          name: step.name,
          description: step.description || '',
          is_proxy: step.is_proxy,
          connection_groups: step.connection_groups,
          message: step.message,
          template_id: data.template_id,
          template_name: templateToInstance.value.name,
          variables: data.variables,
          inputs_mapping: data.inputs_mapping,
          outputs_mapping: data.outputs_mapping,
        },
        type: 'template-instance',
      }));

      addNodes(stepNodes);
      stepNodes.forEach((node) => showNode(node.id));
    }

    showTemplateInstanceModal.value = false;
    await fetchBotData();
  } catch (error) {
    console.error('Ошибка при создании инстанса шаблона:', error);
  }
}

const hasChannels = computed(() => {
  return botInfo.value?.channels?.length > 0;
});

const toggleChat = () => {
  showChat.value = !showChat.value;
};

const closeChat = () => {
  showChat.value = false;
};

// TODO: Animation
// watch(
//   () => ({
//     edgeRefs,
//     animations: Object.values(edgeRefs).map((e) => e?.animation),
//     botInfo: botInfo.value,
//   }),
//   async (value, oldValue, onCleanup) => {
// if (!botInfo.value) return;
//
// const firstStep = botInfo.value.first_step_id;
// const graph = Object.fromEntries(
//   botInfo.value.steps.map((step) => [
//     step.id,
//     step.connection_groups
//       .flatMap((group) => group.connections)
//       .map((connection) => connection.next_step_id),
//   ])
// );
//
// async function waitForAnimations() {
//   return new Promise((resolve) => {
//     const interval = setInterval(() => {
//       if (Object.values(edgeRefs).every((edge) => edge?.animation)) {
//         clearInterval(interval);
//         resolve();
//       }
//     }, 20);
//   });
// }
//
// await waitForAnimations();
// const timeline = createTimeline({ loop: true });
//
// function syncAnimations(step, duration = 0, finishedSteps = new Set()) {
//   if (finishedSteps.has(step)) return;
//   const durations = [];
//
//   for (const next of graph[step]) {
//     const animation = edgeRefs[`e${step}-${next}`].animation;
//     durations.push(animation.duration);
//   }
//
//   for (const next of graph[step]) {
//     const animation = edgeRefs[`e${step}-${next}`].animation;
//     timeline.sync(animation, duration);
//     finishedSteps.add(step);
//     syncAnimations(next, Math.max(...durations), finishedSteps);
//   }
// }
//
// syncAnimations(firstStep);
// timeline.play();
//
// onCleanup(() => timeline.cancel());
//   }
// );
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.transition-flow {
  background: linear-gradient(-45deg, rgb(33, 52, 70) 0%, rgb(66, 73, 78) 100%);
}

.vue-flow__handle {
  border: 4px solid rgb(27, 73, 97);
  border-radius: 6px;
  background: rgb(243, 242, 231);
  width: 15px;
  height: 15px;
}

.vue-flow__edge-path {
  stroke: rgb(207, 255, 125);
  stroke-width: 2px;
}

.vue-flow__node-toolbar {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px;
  border: 1px solid rgb(48, 68, 81);
  border-radius: 10px;
  box-shadow: 0 2px 4.9px 0 rgba(0, 0, 0, 0.25);
  background: linear-gradient(0deg, rgb(45, 45, 45), rgb(53, 53, 53) 100%);
}

.vue-flow__node-toolbar button {
  display: flex;
  padding: 5px;
  color: white;
}

.chat-toggle-button {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(49, 49, 49, 1);
  color: #fff;
  cursor: pointer;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.chat-toggle-button:hover {
  background: rgba(60, 60, 60, 1);
}

.chat-toggle-button.active {
  background: rgba(70, 70, 70, 1);
}
</style>
