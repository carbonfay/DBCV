<template>
  <div class="bot-subscribers">
    <label class="label">Подписчики (агенты)</label>

    <div class="selected-bots">
      <button class="add-btn" @click="toggleAdding" v-if="!isAdding">Добавить</button>
      <div v-for="bot in selectedBots" :key="bot.id" class="bot-chip">
        <div class="bot-name-clickable" @click="navigateToBot(bot.id)">
          {{ bot.name || bot.id }}
        </div>
        <span class="remove" @click="removeBot(bot)">×</span>
      </div>
    </div>

    <transition name="fade">
      <div v-if="isAdding" class="add-panel">
        <input class="search" placeholder="поиск..." v-model="searchQuery" autofocus />
        <div class="bot-list" v-if="availableBotsFiltered.length">
          <div
            v-for="bot in availableBotsFiltered"
            :key="bot.id"
            class="bot-item"
            :class="{ disabled: isSelected(bot.id) }"
            @click="addBot(bot)"
          >
            <span class="bot-avatar">
              <img v-if="bot.avatar" :src="bot.avatar" alt="" />
              <span v-else>{{ (bot.name || bot.id)[0] }}</span>
            </span>
            <span class="bot-name">{{ bot.name || bot.id }}</span>
          </div>
        </div>
        <div v-else class="no-bots">Нет доступных агентов</div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue';
import { useBotsStore } from '@/stores';

const props = defineProps({
  modelValue: Array,
});

const emit = defineEmits(['update:modelValue', 'input']);
const botsStore = useBotsStore();
const searchQuery = ref('');
const isAdding = ref(false);

const selectedBots = computed(() =>
  props.modelValue.filter((subscriber) => subscriber.type === 'bot')
);

const isSelected = (botId) => selectedBots.value.some((bot) => bot.id === botId);
const availableBotsFiltered = computed(() =>
  botsStore.bots.filter(
    (bot) =>
      !isSelected(bot.id) && bot.name?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const toggleAdding = () => {
  isAdding.value = !isAdding.value;
  if (isAdding.value) {
    searchQuery.value = '';
    nextTick(() => {
      const input = document.querySelector('.search');
      if (input) input.focus();
    });
  }
};

const addBot = (bot) => {
  if (!isSelected(bot.id)) {
    const botWithType = { ...bot, type: 'bot' };
    const newValue = [...props.modelValue, botWithType];
    emit('update:modelValue', newValue);
    emit('input', newValue);
    searchQuery.value = '';
  }
};

const removeBot = (bot) => {
  const newValue = props.modelValue.filter((b) => b.id !== bot.id);
  emit('update:modelValue', newValue);
  emit('input', newValue);
};

const navigateToBot = (botId) => {
  window.open(`/bot/${botId}`, '_blank');
};
</script>

<style scoped>
.label {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.2;
  color: #fff;
}

.selected-bots {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 10px;
  align-items: center;
}

.bot-chip {
  background-color: #444;
  padding: 0.4rem 0.7rem;
  border-radius: 0.5rem;
  color: white;
  display: flex;
  align-items: center;
  font-size: 14px;
  line-height: 1.2;
}

.bot-name-clickable {
  color: white;
  cursor: pointer;
}

.bot-name-clickable:hover {
  color: #ffd700;
}

.bot-chip .remove {
  margin-left: 0.5rem;
  cursor: pointer;
  color: red;
}

.add-btn,
.cancel-btn {
  background: #232323;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.4rem 1.1rem;
  font-size: 14px;
  line-height: 1.2;
  transition:
    background 0.15s,
    color 0.15s;
}

.add-btn:hover,
.cancel-btn:hover {
  background: #ffd700;
  color: #232323;
}

.add-panel {
  margin-top: 10px;
}

.bot-list {
  margin-top: 10px;
  padding: 0.4rem 0;
  height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  background: #212121;
  border-radius: 8px;
}

.bot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.4rem 1rem;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.bot-item:hover {
  background-color: #3a3a3a;
  color: #ffd700;
}

.bot-item.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.bot-avatar {
  width: 24px;
  height: 24px;
  background: #444;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  font-weight: bold;
  font-size: 16px;
  overflow: hidden;
}

.bot-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-bots {
  color: #aaa;
  text-align: center;
  padding: 1rem 0;
}

.search {
  display: block;
  background: white;
  width: 100%;
  padding: 8px 28px 8px 14px;
  margin: 10px 0;
  border-radius: 8px;
  font-size: 14px;
  border: 0;
  outline: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
