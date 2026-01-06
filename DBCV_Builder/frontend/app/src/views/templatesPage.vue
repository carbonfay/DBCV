<template>
  <div class="pages-component">
    <div class="container">
      <sidebarMenu />
      <div class="content-block">
        <div class="header-section">
          <div class="buttons-row">
            <div class="card create-card" @click="openCreateTemplateModal">
              <FileIcon class="icon" />
              <div class="text">
                <span>Новый шаблон</span>
                <span class="subtitle">Создание нового шаблона</span>
              </div>
            </div>
            <div class="card create-card" @click="openCreateGroupModal">
              <FileIcon class="icon" />
              <div class="text">
                <span>Новая группа</span>
                <span class="subtitle">Создание новой группы</span>
              </div>
            </div>
          </div>
          <BaseInput v-model="searchQuery" class="dark search-input" placeholder="Поиск шаблонов" />
        </div>
        <BaseLoader v-if="isLoading" />
        <div v-else class="groups-container">
          <div v-for="group in reversedGroups" :key="group.id" class="group-section">
            <div class="group-header">
              <div class="group-info">
                <h3 class="group-title">{{ group.name }}</h3>
                <p v-if="group.description" class="group-description">{{ group.description }}</p>
              </div>
              <div class="group-actions">
                <EditIcon class="icon edit-icon" @click="editGroup(group)" />
                <TrashIcon class="icon" @click="deleteGroup(group.id)" />
              </div>
            </div>
            <div v-if="group.templates.length > 0" class="group-content">
              <div class="card-container">
                <div
                  v-for="template in filteredGroupTemplates(group)"
                  :key="template.id"
                  class="card"
                  @click="openTemplate(template)"
                >
                  <div class="template-actions">
                    <div class="template-action">
                      <i
                        class="fa-solid fa-folder-minus"
                        @click.stop="removeFromGroup(template.id, group.id)"
                      ></i>
                    </div>
                    <div class="template-action">
                      <EditIcon class="icon edit-icon" @click.stop="editTemplate(template)" />
                    </div>
                    <div class="template-action">
                      <TrashIcon class="icon" @click.stop="deleteTemplate(template.id)" />
                    </div>
                  </div>
                  <h3>{{ template.name }}</h3>
                  <div class="card-content">
                    <span class="template-description">{{ template?.description }}</span>
                    <span>Шагов: {{ template.steps?.length || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="group-section">
            <div class="group-header">
              <h3 class="group-title">Другие</h3>
            </div>
            <div v-if="otherTemplates.length > 0" class="group-content">
              <div class="card-container">
                <div
                  v-for="template in filteredOtherTemplates"
                  :key="template.id"
                  class="card"
                  @click="openTemplate(template)"
                >
                  <div class="template-actions">
                    <div class="template-action">
                      <i class="fa-solid fa-folder-plus" @click.stop="addToGroup(template.id)"></i>
                    </div>
                    <div class="template-action">
                      <EditIcon class="icon edit-icon" @click.stop="editTemplate(template)" />
                    </div>
                    <div class="template-action">
                      <TrashIcon class="icon" @click.stop="deleteTemplate(template.id)" />
                    </div>
                  </div>
                  <h3>{{ template.name }}</h3>
                  <div class="card-content">
                    <span class="template-description">{{ template?.description }}</span>
                    <span>Шагов: {{ template.steps?.length || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <templateModal
    v-if="showCreateTemplateModal"
    @close="closeCreateTemplateModal"
    @save="handleCreateTemplate"
  />

  <templateModal
    v-if="showEditModal && templateToEdit"
    :initial="templateToEdit"
    @close="closeEditModal"
    @save="handleEditTemplate"
  />

  <templateViewModal
    v-if="showViewModal && templateToView"
    :template="templateToView"
    @close="closeViewModal"
  />

  <groupModal
    v-if="showCreateGroupModal"
    @close="closeCreateGroupModal"
    @save="handleCreateGroup"
  />

  <groupModal
    v-if="showEditGroupModal && groupToEdit"
    :initial="groupToEdit"
    @close="closeEditGroupModal"
    @save="handleEditGroup"
  />

  <selectGroupModal
    v-if="showSelectGroupModal"
    :groups="templatesGroups"
    @close="closeSelectGroupModal"
    @select-group="handleSelectGroup"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { EditIcon, FileIcon, TrashIcon } from '@/components/icons';
import { useTemplatesStore, useTemplateGroupsStore } from '@/stores';
import sidebarMenu from '@/components/sidebarMenu.vue';
import templateModal from '@/components/modals/templateModal.vue';
import templateViewModal from '@/components/modals/templateViewModal.vue';
import groupModal from '@/components/modals/groupModal.vue';
import selectGroupModal from '@/components/modals/selectGroupModal.vue';
import notyf from '@/plugins/notyf';
import { storeToRefs } from 'pinia';
import type { Template, TemplateGroups } from '@/types/store_types';

const templatesStore = useTemplatesStore();
const templateGroupsStore = useTemplateGroupsStore();

const { templates } = storeToRefs(templatesStore);
const { templatesGroups } = storeToRefs(templateGroupsStore);

const isLoading = ref(true);
const searchQuery = ref('');

const showCreateTemplateModal = ref(false);
const showEditModal = ref(false);
const showViewModal = ref(false);
const showCreateGroupModal = ref(false);
const showEditGroupModal = ref(false);
const showSelectGroupModal = ref(false);

const templateToEdit = ref<Template | null>(null);
const templateToView = ref<Template | null>(null);
const groupToEdit = ref<TemplateGroups | null>(null);
const selectedTemplateId = ref<string>('');

const reversedGroups = computed(() => {
  return [...templatesGroups.value].reverse();
});

const otherTemplates = computed(() =>
  templates.value.filter((template) => template.group === null || template.group === undefined)
);

const filteredOtherTemplates = computed(() => {
  if (!searchQuery.value) return otherTemplates.value;

  const query = searchQuery.value.toLowerCase();
  return otherTemplates.value.filter((template) => {
    const name = template?.name?.toLowerCase() || '';
    const description = template?.description?.toLowerCase() || '';

    return name.includes(query) || description.includes(query);
  });
});

const filteredGroupTemplates = (group: TemplateGroups) => {
  if (!searchQuery.value) return group.templates;

  const query = searchQuery.value.toLowerCase();
  return group.templates.filter((template) => {
    const name = template?.name?.toLowerCase() || '';
    const description = template?.description?.toLowerCase() || '';

    return name.includes(query) || description.includes(query);
  });
};

onMounted(async () => {
  await Promise.all([templatesStore.readTemplates(), templateGroupsStore.readTemplateGroups()]);
  isLoading.value = false;
});

const openCreateTemplateModal = () => {
  showCreateTemplateModal.value = true;
};

const closeCreateTemplateModal = () => {
  showCreateTemplateModal.value = false;
};

const handleCreateTemplate = async (data: any) => {
  const response = await templatesStore.createTemplate(data);
  if (response) {
    notyf.success('Шаблон создан!');
    closeCreateTemplateModal();
  }
};

const editTemplate = (template: Template) => {
  templateToEdit.value = template;
  showEditModal.value = true;
};

const closeEditModal = () => {
  showEditModal.value = false;
  templateToEdit.value = null;
};

const handleEditTemplate = async (data: any) => {
  if (templateToEdit.value) {
    const response = await templatesStore.updateTemplate(templateToEdit.value.id, data);
    if (response) {
      notyf.success('Шаблон обновлен!');
      closeEditModal();
    }
  }
};

const openTemplate = (template: Template) => {
  templateToView.value = template;
  showViewModal.value = true;
};

const closeViewModal = () => {
  showViewModal.value = false;
  templateToView.value = null;
};

const deleteTemplate = async (templateId: string) => {
  if (confirm('Вы уверены, что хотите удалить этот шаблон?')) {
    const response = await templatesStore.deleteTemplate(templateId);
    if (response) {
      notyf.success('Шаблон удален!');
    }
  }
};

const openCreateGroupModal = () => {
  showCreateGroupModal.value = true;
};

const closeCreateGroupModal = () => {
  showCreateGroupModal.value = false;
};

const handleCreateGroup = async (data: any) => {
  const response = await templateGroupsStore.createTemplateGroup(data);
  if (response) {
    notyf.success('Группа создана!');
    closeCreateGroupModal();
  }
};

const editGroup = (group: TemplateGroups) => {
  groupToEdit.value = group;
  showEditGroupModal.value = true;
};

const closeEditGroupModal = () => {
  showEditGroupModal.value = false;
  groupToEdit.value = null;
};

const handleEditGroup = async (data: any) => {
  if (groupToEdit.value) {
    const response = await templateGroupsStore.updateTemplateGroup(groupToEdit.value.id, data);
    if (response) {
      notyf.success('Группа обновлена!');
      closeEditGroupModal();
    }
  }
};

const deleteGroup = async (groupId: string) => {
  if (confirm('Вы уверены, что хотите удалить эту группу?')) {
    const response = await templateGroupsStore.deleteTemplateGroup(groupId);
    if (response) {
      notyf.success('Группа удалена!');
      templatesStore.readTemplates();
    }
  }
};

const addToGroup = (templateId: string) => {
  selectedTemplateId.value = templateId;
  showSelectGroupModal.value = true;
};

const removeFromGroup = async (templateId: string, groupId: string) => {
  if (confirm('Убрать шаблон из группы?')) {
    const response = await templateGroupsStore.removeTemplateFromGroup(groupId, templateId);
    if (response) {
      notyf.success('Шаблон убран из группы!');
    }
  }
};

const closeSelectGroupModal = () => {
  showSelectGroupModal.value = false;
  selectedTemplateId.value = '';
};

const handleSelectGroup = async (groupId: string) => {
  if (selectedTemplateId.value) {
    const response = await templateGroupsStore.addTemplateToGroup(
      groupId,
      selectedTemplateId.value
    );
    if (response) {
      notyf.success('Шаблон добавлен в группу!');
      templatesStore.readTemplates();
    }
  }
  closeSelectGroupModal();
};
</script>

<style src="@/assets/styles/pages.css"></style>

<style scoped>
.header-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 20px;
}

.buttons-row {
  display: flex;
  gap: 15px;
}

.search-input {
  width: 300px;
  margin-bottom: 0;
}

.groups-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.group-section {
  border: 1px solid #404040;
  border-radius: 8px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 15px 20px;
  background: #2a2a2a;
  border-bottom: 1px solid #404040;
}

.group-info {
  flex: 1;
}

.group-title {
  margin: 0 0 5px 0;
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.group-description {
  margin: 0;
  color: #aaa;
  font-size: 13px;
  line-height: 1.3;
}

.group-actions {
  display: flex;
  gap: 10px;
}

.group-content {
  padding: 20px;
}

.empty-group {
  text-align: center;
  color: #888;
  padding: 40px 0;
  font-style: italic;
}

.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.card {
  position: relative;
  background: #313131;
  border: 1px solid #404040;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.card:hover {
  background: #3a3a3a;
  border-color: #555;
}

.card h3 {
  margin: 0 0 10px 0;
  color: white;
  font-size: 16px;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-description {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 8px 0;
  color: #aaa;
}

.card-content {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 4px;
}

.template-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  position: absolute;
  top: 10px;
  right: 10px;
}

.template-action {
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.template-action:hover {
  background: #404040;
}

.icon {
  width: 14px;
  height: 14px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.icon:hover {
  opacity: 1;
}

.add-icon,
.remove-icon {
  font-size: 14px;
  cursor: pointer;
}

.add-icon {
  color: #4caf50;
}

.remove-icon {
  color: #f44336;
}

.edit-icon {
  color: #4caf50;
}

.icon[title*='Удалить'] {
  color: #f44336;
}
</style>
