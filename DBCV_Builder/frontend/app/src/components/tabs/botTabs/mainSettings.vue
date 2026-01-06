<template>
  <div class="bot-settings">
    <form class="form" @submit.prevent="trySave">
      <BaseInput
        v-model="formData.name"
        label="Название"
        required
        @input="isSomethingChanged = true"
      />
      <BaseCodeEditor
        v-model="formData.variables"
        :default-height="100"
        :is-collapsed="false"
        :is-resizable="false"
        class="code-editor"
        label="Переменные"
        language="json"
        light-theme
        small
        @input="isSomethingChanged = true"
      />
      <BaseCodeEditor
        v-model="formData.config"
        :default-height="100"
        :is-collapsed="false"
        :is-resizable="false"
        class="code-editor"
        label="Конфиг"
        language="json"
        light-theme
        small
        @input="isSomethingChanged = true"
      />
      <BaseSelectSearch
        v-model="formData.first_step_id"
        :options="stepOptions"
        label="Первый шаг"
        labelColor="#fff"
        placeholder="Выберите первый шаг"
        @update:model-value="isSomethingChanged = true"
      />
      <BaseButton size="small" styleType="secondary" type="submit">Сохранить</BaseButton>
      <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
    </form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useBotsStore } from '@/stores'; // импорт сторов
import notyf from '@/plugins/notyf';

const props = defineProps({
  botId: {
    type: String,
    required: true,
  },
  botInfo: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['update:botInfo']);

const isSomethingChanged = ref(false);

const botsStore = useBotsStore();
const errorMessage = ref('');
const formData = ref({
  name: props.botInfo?.name || '',
  variables: JSON.stringify(props.botInfo?.variables.data || {}, null, 2),
  first_step_id: props.botInfo?.first_step_id || null,
  config: JSON.stringify(props.botInfo?.config || {}, null, 2),
});

const stepOptions = computed(() => {
  return (
    props.botInfo.steps?.map((step) => ({
      value: step.id,
      label: step.name,
    })) || []
  );
});

// Обновление бота
const trySave = async () => {
  try {
    if (!formData.value.name.trim()) {
      errorMessage.value = 'Название агента не может быть пустым.';
      throw new Error('Название агента не может быть пустым');
    }

    let parsedVariables = {};
    try {
      parsedVariables = JSON.parse(formData.value.variables);
    } catch (error) {
      errorMessage.value = 'Неверный формат JSON в поле "Переменные".';
      throw new Error('Неверный формат JSON в поле "Переменные".');
    }

    let parsedConfig = {};
    try {
      parsedConfig = JSON.parse(formData.value.config);
    } catch (error) {
      errorMessage.value = 'Неверный формат JSON в поле "Конфиг".';
      throw new Error('Неверный формат JSON в поле "Конфиг".');
    }

    await botsStore.updateBot(props.botId, {
      name: formData.value.name,
      variables: {
        data: parsedVariables,
      },
      first_step_id: formData.value.first_step_id,
      config: parsedConfig,
    });

    notyf.success('Сохранено!');
    isSomethingChanged.value = false;
    emit('update:botInfo', {
      ...props.botInfo,
      name: formData.value.name,
      variables: {
        data: parsedVariables,
      },
      first_step_id: formData.value.first_step_id,
      config: parsedConfig,
    });
    errorMessage.value = '';
  } catch (error) {
    notyf.error('Ошибка!');
    errorMessage.value = `Ошибка при сохранении данных агента. ${error.message}`;
    console.error('Ошибка при сохранении данных агента:', error);
    throw error;
  }
};

defineExpose({
  isSomethingChanged,
  trySave,
});
</script>

<style scoped>
* {
  text-transform: none;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form button {
  align-self: flex-end;
}

.code-editor {
  gap: 2px;
}
</style>
