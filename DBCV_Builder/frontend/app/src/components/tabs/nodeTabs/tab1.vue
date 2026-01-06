<template>
  <div class="flex">
    <BaseCopyableId :id="props.node.id" />
    <BaseInput
      v-model="editableNode.name"
      :label="'Название шага'"
      class="section-input"
      @input="isSomethingChanged = true"
    />
    <BaseTextarea
      v-model="editableNode.description"
      :label="'Описание шага'"
      @input="isSomethingChanged = true"
    />
    <BaseCheckbox
      v-model="editableNode.is_proxy"
      :label-color="'rgb(255, 255, 255)'"
      class="section-checkbox"
      @input="isSomethingChanged = true"
    >
      Прокси
    </BaseCheckbox>
    <BaseButton class="button" size="small" styleType="secondary" type="submit" @click="save">
      Сохранить
    </BaseButton>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import notyf from '@/plugins/notyf';

const isSomethingChanged = ref(false);

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const editableNode = ref({
  name: props.node.data.name || '',
  description: props.node.data.description || '',
  is_proxy: props.node.data.is_proxy,
  id: props.node.id,
  type: props.node.type,
});

const emit = defineEmits(['update-node']);

const save = async () => {
  emit('update-node', editableNode.value);
  notyf.success('Сохранено!');
  isSomethingChanged.value = false;
};

defineExpose({ isSomethingChanged, save });
</script>

<style scoped>
.section-input {
  margin-bottom: 10px;
}

.section-checkbox {
  margin: 10px 0;
}

.flex {
  display: flex;
  flex-direction: column;
}

.flex .button {
  align-self: flex-end;
}
</style>
