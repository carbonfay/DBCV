<template>
  <div class="preset-palette">
    <div class="palette-header">
      <h3>Presets</h3>
      <button @click="$emit('close')" class="close-btn">
        <i class="fa-solid fa-times"></i>
      </button>
    </div>
    
    <div class="palette-search">
      <BaseInput
        v-model="searchQuery"
        placeholder="Поиск presets..."
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
      <div v-else-if="filteredPresets.length === 0" class="empty-state">
        <p>Нет доступных presets</p>
      </div>
      <div v-else class="presets-list">
        <div
          v-for="preset in filteredPresets"
          :key="preset.id"
          class="preset-item"
          @click="selectPreset(preset)"
          :style="{ borderLeftColor: preset.color }"
        >
          <div class="preset-icon">
            <img
              v-if="preset.icon_url"
              :src="preset.icon_url"
              :alt="preset.name"
              @error="handleImageError"
            />
            <div v-else class="icon-placeholder" :style="{ backgroundColor: preset.color }">
              {{ preset.name.charAt(0) }}
            </div>
          </div>
          <div class="preset-info">
            <h4>{{ preset.name }}</h4>
            <p>{{ preset.description }}</p>
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
import presetsApi from '@/api/services/presetsApi';

const emit = defineEmits(['select', 'close']);

const presets = ref<any[]>([]);
const isLoading = ref(false);
const searchQuery = ref('');
const selectedCategory = ref<string | null>(null);

const categories = computed(() => {
  const cats = new Set(presets.value.map((p) => p.category));
  return ['all', ...Array.from(cats)];
});

const filteredPresets = computed(() => {
  let filtered = presets.value;

  if (selectedCategory.value && selectedCategory.value !== 'all') {
    filtered = filtered.filter((p) => p.category === selectedCategory.value);
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query)
    );
  }

  return filtered;
});

const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    all: 'Все',
    logic: 'Логика',
    flow: 'Поток',
    integration: 'Интеграции',
  };
  return names[category] || category;
};

const selectPreset = (preset: any) => {
  emit('select', preset);
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
};

const loadPresets = async () => {
  isLoading.value = true;
  try {
    const response = await presetsApi.getCatalog();
    if (response?.data?.items) {
      presets.value = response.data.items;
    }
  } catch (error) {
    console.error('Error loading presets:', error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadPresets();
});
</script>

<style scoped>
.preset-palette {
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

.presets-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preset-item {
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

.preset-item:hover {
  background: rgba(80, 80, 80, 0.7);
  border-color: rgba(116, 116, 116, 0.6);
}

.preset-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preset-icon img {
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

.preset-info {
  flex: 1;
  min-width: 0;
}

.preset-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  font-weight: 600;
}

.preset-info p {
  margin: 0;
  font-size: 0.75rem;
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

