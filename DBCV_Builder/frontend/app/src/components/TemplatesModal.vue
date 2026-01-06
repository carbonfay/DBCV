<template>
  <div class="templates-modal-content">
    <div class="group-header">
      <h3>{{ groupName }}</h3>
      <div class="header-actions">
        <button v-if="group?.id == 'other'" class="create-btn" @click="openCreateTemplateModal">
          <i class="fas fa-plus"></i>
          Создать
        </button>
      </div>
    </div>
    <div class="search-container">
      <BaseInput v-model="searchQuery" class="dark" placeholder="Поиск" />
    </div>
    <div class="modal-content">
      <div v-if="isLoading" class="loading">
        <BaseLoader />
      </div>
      <div v-else-if="templates.length === 0" class="empty-state">Нет шаблонов в этой группе</div>
      <ul v-else class="templates-list">
        <li
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-item"
          draggable="true"
          @click="openTemplate(template)"
          @dragstart="onDragStart($event, template)"
        >
          <div class="template-main">
            <span class="template-name">{{ template.name }}</span>
            <div class="template-steps-count">Шагов: {{ template.steps?.length ?? 0 }}</div>
          </div>
        </li>
      </ul>
    </div>
  </div>
  <templateModal
    v-if="showTemplateModal"
    :botId="botId"
    :steps="stepsForTemplate"
    :initial="templateToEdit"
    @close="closeTemplateModal"
    @save="saveTemplate"
  />
  <templateViewModal
    v-if="showViewModal && templateToView"
    :template="templateToView"
    @close="closeViewModal"
  />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { EditIcon, TrashIcon } from '@/components/icons';
import templateModal from '@/components/modals/templateModal.vue';
import templateViewModal from '@/components/modals/templateViewModal.vue';
import { useTemplatesStore } from '@/stores';

const props = defineProps({
  group: {
    type: Object,
    required: true,
  },
  botId: {
    type: String,
    required: true,
  },
  show: {
    type: Boolean,
    required: true,
  },
  nodes: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['close', 'action']);

const templatesStore = useTemplatesStore();
const isLoading = ref(false);
const showTemplateModal = ref(false);
const templateToEdit = ref(null);
const templates = ref([]);
const showViewModal = ref(false);
const showEditModal = ref(false);
const templateToView = ref(null);
const searchQuery = ref('');

const filteredTemplates = computed(() => {
  if (!searchQuery.value) {
    return templates.value;
  }

  const query = searchQuery.value.toLowerCase();
  return templates.value.filter((template) => template.name.toLowerCase().includes(query));
});

const groupName = computed(() => props.group?.name);

const stepsForTemplate = computed(() =>
  props.nodes.filter((n) => n.type === 'simple').map((n) => ({ id: n.id, name: n.data.name }))
);

const updateTemplatesList = (group) => {
  if (group.id === 'other') {
    loadAllTemplates();
  } else {
    templates.value = group.templates || [];
  }
};

const loadAllTemplates = async () => {
  isLoading.value = true;
  await templatesStore.readTemplates();
  templates.value = templatesStore.templates;
  isLoading.value = false;
};

const onDragStart = (event, template) => {
  event.dataTransfer.setData(
    'application/json',
    JSON.stringify({
      type: 'template',
      template: template,
    })
  );
  event.dataTransfer.effectAllowed = 'copy';
};

function openTemplate(template) {
  templateToView.value = template;
  showViewModal.value = true;
}

const closeViewModal = () => {
  showViewModal.value = false;
  templateToView.value = null;
};

const openCreateTemplateModal = () => {
  templateToEdit.value = null;
  showTemplateModal.value = true;
};

const closeTemplateModal = () => {
  showTemplateModal.value = false;
  templateToEdit.value = null;
};

const saveTemplate = async (data) => {
  if (templateToEdit.value) {
    await templatesStore.updateTemplate(templateToEdit.value.id, data);
  } else {
    await templatesStore.createTemplate(data);
  }
  closeTemplateModal();
  updateTemplatesList(props.group);
};

onMounted(() => {
  updateTemplatesList(props.group);
});
</script>

<style scoped>
.templates-modal-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid rgb(48, 68, 81);
}

.group-header h3 {
  margin: 0;
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.modal-content {
  padding: 15px 0;
  flex: 1;
  overflow-y: auto;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.empty-state {
  text-align: center;
  color: #888;
  padding: 40px 0;
  font-style: italic;
  font-size: 13px;
}

.templates-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.template-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid rgb(48, 68, 81);
  border-radius: 5px;
  margin-bottom: 8px;
  background: rgb(53, 53, 53);
  cursor: pointer;
  transition: background-color 0.2s;
}

.template-item:hover {
  background: rgb(60, 60, 60);
}

.template-main {
  flex: 1;
}

.template-name {
  display: block;
  color: white;
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 13px;
}

.template-steps-count {
  color: #8bc34a;
  font-size: 11px;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 14px;
  height: 14px;
  opacity: 0.7;
  cursor: pointer;
  transition: opacity 0.2s;
}

.icon-btn:hover {
  opacity: 1;
}

.search-container {
  padding: 15px 0;
  border-bottom: 1px solid rgb(48, 68, 81);
}
</style>
