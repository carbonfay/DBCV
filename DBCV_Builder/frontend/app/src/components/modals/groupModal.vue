<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal">
      <div class="modal-head">
        <div class="modal-title">{{ isEdit ? 'Редактировать группу' : 'Создать группу' }}</div>
        <button class="modal-close" @click="close">×</button>
      </div>
      <form @submit.prevent="handleSave">
        <BaseInput v-model="form.name" required label="Название *" class="dark" />
        <BaseInput v-model="form.description" label="Описание" class="dark" />

        <div class="modal-footer">
          <button type="button" class="btn secondary" @click="close">Отмена</button>
          <button type="submit" class="btn primary">
            {{ isEdit ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineEmits, defineProps } from 'vue';

const props = defineProps({
  initial: { type: Object, default: null },
});

const emit = defineEmits(['close', 'save']);

const isEdit = computed(() => !!props.initial);

const form = ref({
  name: '',
  description: '',
});

const error = ref('');

watch(
  () => props.initial,
  (val) => {
    if (val) {
      form.value.name = val.name || '';
      form.value.description = val.description || '';
    }
  },
  { immediate: true }
);

function close() {
  emit('close');
}

function handleSave() {
  error.value = '';

  if (!form.value.name.trim()) {
    error.value = 'Название обязательно';
    return;
  }

  emit('save', {
    name: form.value.name,
    description: form.value.description,
  });
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow: auto;
  padding: 30px 0;
}

.modal {
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
  padding: 20px;
  min-width: 400px;
  width: 100%;
  max-width: 500px;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-title {
  text-transform: uppercase;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #fff;
}

form {
  display: grid;
  gap: 15px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn.primary {
  background: #4caf50;
  color: #fff;
}

.btn.secondary {
  background: #6c757d;
  color: #fff;
}

.error {
  color: #f44336;
  margin-top: 10px;
  text-align: center;
}
</style>
