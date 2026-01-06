<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal">
      <div class="modal-head">
        <div class="modal-title">Выберите группу</div>
        <button class="modal-close" @click="close">×</button>
      </div>
      <div class="modal-content">
        <div v-if="groups.length === 0" class="empty-groups">Нет доступных групп</div>
        <div v-else class="groups-list">
          <div
            v-for="group in groups"
            :key="group.id"
            class="group-item"
            @click="selectGroup(group.id)"
          >
            <div class="group-info">
              <h4>{{ group.name }}</h4>
              <p v-if="group.description" class="group-desc">{{ group.description }}</p>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn secondary" @click="close">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  groups: { type: Array, default: () => [] },
});

const emit = defineEmits(['close', 'select-group']);

function close() {
  emit('close');
}

function selectGroup(groupId) {
  emit('select-group', groupId);
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
  align-items: center;
  justify-content: center;
}

.modal {
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
  padding: 20px;
  min-width: 400px;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
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

.modal-content {
  margin-bottom: 20px;
}

.empty-groups {
  text-align: center;
  color: #888;
  padding: 40px 0;
  font-style: italic;
}

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-item {
  padding: 12px;
  border: 1px solid #404040;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.group-item:hover {
  background: #3a3a3a;
}

.group-info h4 {
  margin: 0 0 5px 0;
  color: white;
  font-size: 14px;
}

.group-desc {
  margin: 0;
  color: #aaa;
  font-size: 12px;
  line-height: 1.3;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn.secondary {
  background: #6c757d;
  color: #fff;
}
</style>
