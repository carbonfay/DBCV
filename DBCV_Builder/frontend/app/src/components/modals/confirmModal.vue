<template>
  <div class="confirm-modal-overlay" @click.self="closeConfirmModal">
    <div class="confirm-modal">
      <div class="confirm-modal-content">
        <p class="confirm-text">Сохранить изменения?</p>
        <BaseButton styleType="danger-dark" size="medium" @click="handleDiscard">
          Не сохранять
        </BaseButton>
        <BaseButton styleType="primary" size="medium" @click="handleSave">
          Сохранить и закрыть
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
const emit = defineEmits<{
  (e: 'close'): void; // Событие для закрытия попаппа
  (e: 'close-main'): void; // Событие для закрытия основного попапа
  (e: 'confirm', save: boolean): void; // Событие для подтверждения с указанием необходимости сохранения
}>();

// Функция для закрытия подтверждающего попапа
const closeConfirmModal = () => {
  emit('close');
};

// Функция, вызываемая при нажатии "Не сохранять"
const handleDiscard = () => {
  emit('close');
  emit('close-main');
};

// Функция, вызываемая при нажатии "Сохранить и закрыть"
const handleSave = () => {
  emit('confirm', true);
  emit('close');
};
</script>

<style scoped>
.confirm-modal-overlay {
  display: grid;
  align-items: center;
  justify-content: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1001;
}

.confirm-modal {
  max-width: 100%;
  padding: 10px 15px;
  background: #ffffff;
  border: 2px solid #d9d9d9;
  border-radius: 10px;
}

.confirm-modal-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.confirm-text {
  font-size: 16px;
  font-weight: 700;
  color: #1e1e1e;
}
</style>
