<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal">
      <div class="modal-head">
        <div class="modal-title">Шаблон: {{ template.name }}</div>
        <button class="modal-close" @click="close">×</button>
      </div>
      <div class="modal-section copyable-id">
        <BaseCopyableId :id="template.id" />
      </div>
      <div class="modal-section">
        <div class="section-label">Описание:</div>
        <div>{{ template.description || '—' }}</div>
      </div>
      <button v-if="template?.bot_id" @click="goToBot" class="btn primary">
        Перейти к агенту для редактирования
      </button>
      <div class="modal-section">
        <div class="section-label">Первый шаг:</div>
        <div>
          {{
            template.steps?.find((s) => s.id === template.first_step_id)?.name ||
            template.first_step_id
          }}
          <span v-if="template.first_step_id">({{ template.first_step_id }})</span>
        </div>
      </div>
      <div class="modal-section">
        <div class="section-label">Шаги:</div>
        <ul>
          <li v-for="step in template.steps" :key="step.id">{{ step.name }} ({{ step.id }})</li>
        </ul>
      </div>
      <div class="modal-section">
        <div class="section-label">Переменные:</div>
        <pre class="json-block">{{ formatJson(template.variables) }}</pre>
      </div>
      <div class="modal-section">
        <div class="section-label">Inputs:</div>
        <pre class="json-block">{{ formatJson(template.inputs) }}</pre>
      </div>
      <div class="modal-section">
        <div class="section-label">Outputs:</div>
        <pre class="json-block">{{ formatJson(template.outputs) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({ template: Object });
const emit = defineEmits(['close']);

function close() {
  emit('close');
}

function formatJson(obj) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

function goToBot() {
  if (props.template?.bot_id) {
    window.open(`/bot/${props.template.bot_id}`, '_blank');
  }
}
</script>

<style scoped>
* {
  text-transform: none;
  font-size: 12px;
}

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
  padding: 10px 15px;
  min-width: 300px;
  width: 100%;
  max-width: 800px;
  display: grid;
  align-items: start;
  gap: 10px;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}

.section-label {
  font-size: 12px;
  font-weight: 800;
  line-height: 140%;
  letter-spacing: normal;
  text-transform: uppercase;
  color: #4caf50;
}

.json-block {
  background: #212121;
  border-radius: 8px;
  padding: 8px;
  font-size: 13px;
  font-family: monospace;
  white-space: pre-wrap;
}

.copyable-id {
  position: relative;
  top: -5px;
}

.btn.primary {
  background: #4caf50;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 15px;
  margin-bottom: 10px;
}
</style>
