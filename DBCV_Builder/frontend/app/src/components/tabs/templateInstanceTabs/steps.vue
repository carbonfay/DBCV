<template>
  <div class="flex">
    <div class="section">
      <p class="section-description">Шаги, включенные в этот шаблон, и их конфигурация</p>
      <div class="first-step-section">
        <h4 class="subsection-title">Первый шаг</h4>
        <div class="step-card first-step">
          <span class="step-name">{{ firstStep?.name || 'N/A' }}</span>
          <span class="step-id">ID: {{ firstStep?.id || 'N/A' }}</span>
        </div>
      </div>
      <div class="all-steps-section">
        <h4 class="subsection-title">Все шаги ({{ templateSteps.length }})</h4>
        <div class="steps-list">
          <div
            v-for="step in templateSteps"
            :key="step.id"
            class="step-card"
            :class="{ 'is-first-step': step.id === firstStep?.id }"
          >
            <span v-if="step.id === firstStep?.id" class="first-step-badge">First</span>
            <span class="step-name">{{ step.name }}</span>
            <span class="step-id">ID: {{ step.id }}</span>
            <div class="step-details">
              <span class="step-detail">
                <strong>Proxy:</strong>
                {{ step.is_proxy ? 'Yes' : 'No' }}
              </span>
              <span class="step-detail">
                <strong>Connections:</strong>
                {{ getConnectionsCount(step) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const templateSteps = computed(() => {
  if (props.node.data.template_instance?.steps) {
    return props.node.data.template_instance.steps;
  }
  return props.node.data.steps || [];
});

const firstStep = computed(() => {
  const firstStepId = props.node.data.template_instance?.first_step_id;
  if (firstStepId) {
    const found = templateSteps.value.find((step) => step.id === firstStepId);
    return found;
  }
  return templateSteps.value[0];
});

const getConnectionsCount = (step) => {
  if (!step.connection_groups) return 0;
  return step.connection_groups.reduce((total, group) => {
    return total + (group.connections?.length || 0);
  }, 0);
};

defineExpose({});
</script>

<style scoped>
.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 193, 7);
  margin-bottom: 10px;
}

.section-description {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 15px;
  line-height: 1.2;
}

.subsection-title {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.2;
  color: #fff;
  margin: 0 0 6px;
}

.first-step-section {
  margin-bottom: 25px;
}

.first-step {
  border: 2px solid rgb(255, 193, 7);
  background: rgba(255, 193, 7, 0.1);
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-card {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
}

.step-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.step-card.is-first-step {
  border-color: rgb(255, 193, 7);
  background: rgba(255, 193, 7, 0.1);
}

.step-name {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  flex: 1;
}

.step-id {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-family: monospace;
}

.first-step-badge {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 193, 7);
  background: rgba(255, 193, 7, 0.2);
  padding: 2px 6px;
  border-radius: 3px;
  width: fit-content;
  margin: 0 0 6px;
}

.step-details {
  display: flex;
  gap: 15px;
}

.step-detail {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
}

.step-detail strong {
  color: rgba(255, 255, 255, 0.8);
}

.flex {
  display: flex;
  flex-direction: column;
}
</style>
