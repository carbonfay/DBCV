<template>
  <div>
    <p class="section-text">
      Настройте сообщение, которое будет отправлять агент при активации этого шага.
    </p>
    <BaseButton
      v-if="!isMessageCreated"
      class="add-message"
      size="small"
      styleType="secondary"
      @click.stop="showMessageForm"
    >
      Создать сообщение
    </BaseButton>
    <div v-if="isMessageCreated" class="flex">
      <BaseTextarea
        v-model="messageData.text"
        :label="'Текст'"
        class="custom-textarea"
        @input="isSomethingChanged = true"
      />
      <div class="widgets-block">
        <BaseSelectSearch
          v-model="selectedId"
          :label="'Виджеты'"
          :labelColor="'rgb(255, 255, 255)'"
          :options="options"
          @input="isSomethingChanged = true"
          @update:modelValue="handleWidgetSelect"
        />
        <button
          :disabled="!selectedWidget"
          class="widget-action-btn edit-btn"
          @click="openEditWidgetModal"
        >
          <EditIcon class="icon" />
        </button>
        <button class="widget-action-btn create-btn" @click="openCreateWidgetModal">+</button>
      </div>
      <div v-if="selectedWidget" class="widget-card">
        <p>{{ selectedWidget.name }}</p>
        <p>
          <strong>Описание:</strong>
          {{ selectedWidget.description || 'Нет описания' }}
        </p>
        <p>
          <strong>ID:</strong>
          {{ selectedWidget.id }}
        </p>
        <button class="btn-clear" @click="clearWidgetSelection">x</button>
      </div>
      <!-- <BaseInput v-model="messageData.sender_id" :label="'Отправитель'" :placeholder="'id отправитель'" :hint="'Оставьте пустым, если отправитель - тот же бот'" class="custom-input"/> -->
      <BaseInput
        v-model="messageData.recipient_id"
        :hint="'Оставьте пустым, если получатель - получатель из сессии'"
        :label="'Получатель'"
        :placeholder="'id получатель'"
        class="custom-input"
        @input="isSomethingChanged = true"
      />
      <BaseInput
        v-model="messageData.channel_id"
        :label="'Канал'"
        :placeholder="'id канала'"
        class="custom-input"
        @input="isSomethingChanged = true"
      />
      <BaseCodeEditor
        v-model="messageData.params"
        :default-height="100"
        :is-collapsed="false"
        :is-resizable="false"
        :auto-height="true"
        class="code-editor"
        label="Параметры"
        language="json"
        light-theme
        small
        @input="isSomethingChanged = true"
      />
      <div class="btns-block">
        <button class="btn-delete" @click="deleteMessage">
          <TrashIcon class="icon" />
        </button>
        <BaseButton class="btn-save" size="small" styleType="secondary" @click="save">
          Сохранить
        </BaseButton>
      </div>
    </div>
    <widgetModal
      v-if="isWidgetModalOpen"
      :currentWidgetId="currentWidgetId"
      :formData="currentFormData"
      :isEditMode="isEditMode"
      @close="closeWidgetModal"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useMessagesStore, useWidgetsStore } from '@/stores'; // импорт stores
import { EditIcon, TrashIcon } from '@/components/icons'; // импорт иконок
import notyf from '@/plugins/notyf';
import widgetModal from '@/components/modals/widgetModal.vue';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const isSomethingChanged = ref(false);

const widgetsStore = useWidgetsStore();
const messagesStore = useMessagesStore();

const selectedWidget = ref(null);
const selectedId = ref('');
const isMessageCreated = ref(false);

const widgets = computed(() => [...widgetsStore.widgets].reverse());

const emit = defineEmits(['graphUpdate-node']);

const messageData = ref({
  id: '',
  text: '',
  recipient_id: '',
  widget_id: '',
  channel_id: '',
  attachments: [],
  params: '',
});

// Показать форму для создания сообщения
const showMessageForm = () => {
  isMessageCreated.value = true;
};

// Опции для селекта
const options = computed(() => {
  if (!widgets.value || widgets.value.length === 0) {
    return [{ value: '', label: '...' }];
  }
  return widgets.value.map((widget) => ({
    value: widget.id,
    label: widget.name || `Виджет ${widget.id}`,
  }));
});

// Обработчик выбора виджета
const handleWidgetSelect = (selectedId) => {
  if (!selectedId) {
    selectedWidget.value = null;
    messageData.value.widget_id = '';
    return;
  }
  const widget = widgets.value.find((w) => w.id === selectedId);
  selectedWidget.value = widget || null;
  messageData.value.widget_id = widget?.id || '';
};

// Очистить при удалении виджета
const clearWidgetSelection = () => {
  selectedId.value = '';
  selectedWidget.value = null;
  messageData.value.widget_id = '';
};

// Сохранить сообщение
const save = async () => {
  const additionalData =
    props.node.type === 'simple' ? { step_id: props.node.id } : { emitter_id: props.node.id };
  if (messageData.value.id) {
    const updateData = {
      text: messageData.value.text || null,
      params: JSON.parse(messageData.value.params),
      recipient_id: messageData.value.recipient_id || null,
      widget_id: messageData.value.widget_id || null,
      channel_id: messageData.value.channel_id || null,
      ...additionalData,
    };
    await messagesStore.updateMessage(messageData.value.id, updateData);
  } else {
    const response = await messagesStore.createMessage({
      ...messageData.value,
      ...additionalData,
    });
    messageData.value.id = response.id;
  }
  notyf.success('Сохранено!');
  isSomethingChanged.value = false;
  emit('graphUpdate-node', { id: props.node.id, data: messageData.value });
};

// Удалить сообщение
const deleteMessage = async () => {
  if (messageData.value.id) {
    await messagesStore.deleteMessage(messageData.value.id);
    isSomethingChanged.value = false;
    emit('graphUpdate-node', { id: props.node.id, data: messageData.value });
  }
  resetForm();
};

// Сброс формы
const resetForm = () => {
  isMessageCreated.value = false;
  messageData.value = {
    text: '',
    recipient_id: '',
    widget_id: '',
    channel_id: '',
    attachments: [],
    params: '',
  };
  selectedId.value = '';
  selectedWidget.value = null;
  isSomethingChanged.value = false;
};

const initializeBlocks = async () => {
  const response = ref(props.node.data.message);
  const existingMessage = response.value;
  if (existingMessage) {
    isMessageCreated.value = true;
    messageData.value = {
      id: existingMessage.id || '',
      text: existingMessage.text || '',
      sender_id: existingMessage.sender_id || '',
      recipient_id: existingMessage.recipient_id || '',
      widget_id: existingMessage.widget_id || '',
      channel_id: existingMessage.channel_id || '',
      attachments: existingMessage.attachments || [],
      params: JSON.stringify(existingMessage.params || {}, null, 2),
    };
    selectedId.value = existingMessage.widget_id || '';
    selectedWidget.value = widgets.value.find((w) => w.id === existingMessage.widget_id) || null;
  }
};

defineExpose({ isSomethingChanged, save });

onMounted(async () => {
  await widgetsStore.readWidgets();
  await initializeBlocks();
});

const isWidgetModalOpen = ref(false);
const isEditMode = ref(false);
const currentWidgetId = ref(null);

const currentFormData = ref({
  name: '',
  description: '',
  js: '',
  css: '',
  body: '',
});

// Открыть модалку для создания виджета
const openCreateWidgetModal = () => {
  isEditMode.value = false;
  currentWidgetId.value = null;
  currentFormData.value = {
    name: '',
    description: '',
    js: '',
    css: '',
    body: '',
  };
  isWidgetModalOpen.value = true;
};

// Открыть модалку для редактирования виджета
const openEditWidgetModal = () => {
  if (!selectedWidget.value) return;

  isEditMode.value = true;
  currentWidgetId.value = selectedWidget.value.id;

  const widget = widgetsStore.widgets.find((wid) => wid.id === selectedWidget.value.id);
  if (widget) {
    Object.assign(currentFormData.value, widget);
  } else {
    console.error('Виджет с указанным ID не найден');
  }

  isWidgetModalOpen.value = true;
};

// Закрытие модального окна реквестов
const closeWidgetModal = () => {
  isWidgetModalOpen.value = false;
  selectedWidget.value = widgetsStore.widgets.find((wid) => wid.id === selectedWidget.value.id);
};
</script>

<style scoped>
.flex {
  display: flex;
  flex-direction: column;
}

.section-text {
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
}

.widget-card {
  padding: 10px 30px 10px 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #434343;
  margin: 10px 0 0;
  position: relative;
}

.widget-card p {
  font-size: 12px;
  overflow: auto;
}

.custom-textarea {
  margin: 10px 0;
}

.custom-input {
  margin: 10px 0 0;
}

.btn-clear {
  position: absolute;
  right: 15px;
  top: 5px;
  font-size: 15px;
}

.btns-block {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
}

.add-message {
  margin: 10px 0 0;
  width: 100%;
}

.icon {
  height: 16px;
  width: auto;
  margin-right: 10px;
  stroke: #fff;
}

.code-editor {
  gap: 2px;
  margin: 10px 0;
}

.widgets-block {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

button.widget-action-btn {
  border: 1px solid rgb(217, 217, 217);
  background-color: #fff;
  border-radius: 8px;
  padding: 8px;
  font-size: 14px;
  font-weight: 600;
  width: 100%;
  max-width: 34px;
  height: 34px;
  color: #000;
}

button.widget-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
