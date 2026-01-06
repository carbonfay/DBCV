<template>
  <div class="copyable-id" @click="copyId">
    <button class="copy-button">
      <svg
        v-if="!copied"
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          d="M16 1H4C2.897 1 2 1.897 2 3v14h2V3h12V1zm3 4H8c-1.103 0-2 .897-2 2v14c0 1.103.897 2 2 2h11c1.103 0 2-.897 2-2V7c0-1.103-.897-2-2-2zm0 16H8V7h11v14z"
        />
      </svg>
      <svg
        v-else
        class="checkmark"
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        fill="#fff"
        viewBox="0 0 24 24"
      >
        <path d="M20.285 6.709l-11.285 11.29-5.285-5.289 1.414-1.414 3.871 3.875 9.871-9.875z" />
      </svg>
    </button>
    <span class="id-text">{{ id }}</span>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseCopyableId',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  id: string | number;
}

const props = defineProps<Props>();

const copied = ref(false);

const copyId = async () => {
  try {
    await navigator.clipboard.writeText(String(props.id));
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 1200);
  } catch (err) {
    console.error('Ошибка при копировании:', err);
  }
};
</script>

<style scoped>
.copyable-id {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #8b8b8b;
  cursor: pointer;
}

.copy-button {
  padding: 2px;
  color: #8b8b8b;
  transition: color 0.2s ease;
}

.copy-button:hover {
  color: #fff;
}

.copy-button:focus {
  outline: none;
}

.checkmark {
  transition: opacity 0.2s ease;
}
</style>
