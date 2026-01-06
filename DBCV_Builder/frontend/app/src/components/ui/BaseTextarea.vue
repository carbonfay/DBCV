<template>
  <div class="textarea-wrapper">
    <label v-if="label" :style="{ color: labelColor }" class="textarea-label">{{ label }}</label>
    <textarea
      ref="textareaRef"
      :placeholder="placeholder"
      :rows="rows"
      :style="{ color: textColor, backgroundColor: backgroundColor, border: border }"
      v-model="model"
      class="textarea"
      @input="callAutoResize"
    ></textarea>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseTextarea',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Props {
  label?: string;
  labelColor?: string;
  textColor?: string;
  backgroundColor?: string;
  border?: string;
  rows?: number;
  placeholder?: string;
  maxHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  label: '',
  labelColor: 'rgb(255, 255, 255)',
  textColor: 'rgb(30, 30, 30)',
  backgroundColor: '#fff',
  border: '1px solid rgb(217, 217, 217)',
  rows: 3,
  placeholder: '',
  maxHeight: '200px',
});

const model = defineModel<string>({ default: '' });
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const callAutoResize = () => {
  if (!textareaRef.value) return;

  textareaRef.value.style.height = 'auto';

  const newHeight = `${textareaRef.value.scrollHeight}px`;

  textareaRef.value.style.height = `min(${newHeight}, ${props.maxHeight})`;
};

onMounted(() => {
  callAutoResize();
});
</script>

<style scoped>
.textarea-wrapper {
  display: flex;
  flex-direction: column;
}

.textarea-label {
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
}

.textarea {
  border-radius: 8px;
  font-size: 14px;
  font-weight: 400;
  line-height: 140%;
  letter-spacing: normal;
  width: 100%;
  padding: 12px 16px;
  max-width: 100%;
  resize: vertical;
}
</style>
