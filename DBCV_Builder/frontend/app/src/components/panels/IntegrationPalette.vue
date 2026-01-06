<template>
  <div class="integration-palette">
    <div class="palette-header">
      <h3>Интеграции</h3>
      <button @click="$emit('close')" class="close-btn">
        <i class="fa-solid fa-times"></i>
      </button>
    </div>
    
    <div class="palette-search">
      <BaseInput
        v-model="searchQuery"
        placeholder="Поиск интеграций..."
        class="search-input"
      />
    </div>
    
    <div class="palette-tabs">
      <button
        v-for="category in categories"
        :key="category"
        @click="selectedCategory = category"
        :class="['tab-btn', { active: selectedCategory === category }]"
      >
        {{ getCategoryName(category) }}
      </button>
    </div>
    
    <div class="palette-content">
      <BaseLoader v-if="isLoading" />
      <div v-else-if="filteredIntegrations.length === 0" class="empty-state">
        <p>Интеграции не найдены</p>
      </div>
      <div v-else class="integrations-list">
        <div
          v-for="integration in filteredIntegrations"
          :key="integration.id"
          class="integration-item"
          @click="selectIntegration(integration)"
          :style="{ borderLeftColor: integration.color }"
        >
          <div class="integration-icon">
            <img
              v-if="integration.icon_url"
              :src="integration.icon_url"
              :alt="integration.name"
              @error="handleImageError"
            />
            <div v-else class="icon-placeholder" :style="{ backgroundColor: integration.color }">
              {{ integration.name.charAt(0) }}
            </div>
          </div>
          <div class="integration-info">
            <h4>{{ integration.name }}</h4>
            <p>{{ integration.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import BaseInput from '@/components/ui/BaseInput.vue';
import BaseLoader from '@/components/ui/BaseLoader.vue';
import integrationsApi from '@/api/services/integrationsApi';

const emit = defineEmits(['select', 'close']);

const integrations = ref<any[]>([]);
const isLoading = ref(false);
const searchQuery = ref('');
const selectedCategory = ref<string | null>(null);

const categories = computed(() => {
  const cats = new Set(integrations.value.map((i) => i.category));
  return ['all', ...Array.from(cats)];
});

const filteredIntegrations = computed(() => {
  let filtered = integrations.value;

  // Фильтр по категории
  if (selectedCategory.value && selectedCategory.value !== 'all') {
    filtered = filtered.filter((i) => i.category === selectedCategory.value);
  }

  // Фильтр по поиску
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      (i) =>
        i.name.toLowerCase().includes(query) ||
        i.description.toLowerCase().includes(query)
    );
  }

  return filtered;
});

const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    all: 'Все',
    messaging: 'Мессенджеры',
    ai: 'AI',
    storage: 'Хранилища',
    weather: 'Погода',
    maps: 'Карты',
    payments: 'Платежи',
    crm: 'CRM',
    ecommerce: 'E-commerce',
    education: 'Образование',
    medicine: 'Медицина',
    news: 'Новости',
    translation: 'Переводы',
  };
  return names[category] || category;
};

const selectIntegration = (integration: any) => {
  emit('select', integration);
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
};

const loadIntegrations = async () => {
  isLoading.value = true;
  try {
    const response = await integrationsApi.getCatalog();
    if (response?.data?.items) {
      integrations.value = response.data.items;
    }
  } catch (error) {
    console.error('Error loading integrations:', error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadIntegrations();
});
</script>

<style scoped>
.integration-palette {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #2d2d2d;
  color: #fff;
}

.palette-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid rgba(116, 116, 116, 0.3);
}

.palette-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(116, 116, 116, 0.3);
  color: #fff;
}

.palette-search {
  padding: 1rem;
  border-bottom: 1px solid rgba(116, 116, 116, 0.3);
}

.palette-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-bottom: 1px solid rgba(116, 116, 116, 0.3);
  overflow-x: auto;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(116, 116, 116, 0.5);
  border-radius: 4px;
  background: rgba(60, 60, 60, 0.8);
  color: #fff;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  background: rgba(80, 80, 80, 0.9);
}

.tab-btn.active {
  background: rgba(0, 145, 255, 0.8);
  border-color: rgba(0, 145, 255, 1);
}

.palette-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #888;
}

.integrations-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.integration-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgba(116, 116, 116, 0.3);
  border-left: 4px solid;
  border-radius: 4px;
  background: rgba(60, 60, 60, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.integration-item:hover {
  background: rgba(80, 80, 80, 0.7);
  border-color: rgba(116, 116, 116, 0.6);
}

.integration-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.integration-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.icon-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  font-size: 1.2rem;
}

.integration-info {
  flex: 1;
  min-width: 0;
}

.integration-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  font-weight: 600;
}

.integration-info p {
  margin: 0;
  font-size: 0.75rem;
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

