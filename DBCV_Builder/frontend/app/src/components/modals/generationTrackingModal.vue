<template>
  <div class="modal-overlay" @click="closeModal">
    <div class="modal tracking-modal" @click.stop>
      <div class="modal-head">
        <div class="modal-name">Отслеживание генерации бота</div>
        <div class="modal-options">
          <button class="modal-close" @click.prevent="closeModal">
            <CloseIcon />
          </button>
        </div>
      </div>
      
      <GenerationTracker
        v-if="sessionId"
        :session-id="sessionId"
        @close="closeModal"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { CloseIcon } from '@/components/icons';
import GenerationTracker from '@/components/tracking/GenerationTracker.vue';

interface GenerationTrackingModalProps {
  sessionId: string;
}

const props = defineProps<GenerationTrackingModalProps>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();

const closeModal = () => {
  emit('close');
};
</script>

<style scoped>
.modal-overlay {
  display: grid;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 30px 0;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.tracking-modal {
  width: 90vw;
  max-width: 1200px;
  max-height: 90vh;
  display: grid;
  align-items: start;
  grid-template-rows: auto 1fr;
  gap: 10px;
  padding: 10px 15px;
  background: #313131;
  border: 1px solid #747474;
  border-radius: 10px;
  overflow: hidden;
}

.modal-head {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
}

.modal-name {
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
}

.modal-options {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 5px;
}

.modal-close {
  display: grid;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  transition-duration: 0.1s;
  transition-property: transform, background, box-shadow;
  transition-timing-function: linear;
}

.modal-close:hover {
  background: #00000044;
}

.modal-close:active {
  background: #00000044;
  transform: translate(2px, 2px);
  box-shadow: none;
}
</style>
