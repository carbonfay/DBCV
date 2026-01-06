<template>
  <div :class="{ collapsed: isCollapsed || !isResizable }" class="resizable-editor">
    <div :class="{ resizable: isResizable }" class="label-area" @click="toggle">
      <label :style="{ color: labelColor }" class="label-text">
        {{ label }}
      </label>
      <span v-if="isResizable" class="label-flag">{{ isCollapsed ? 'Раскрыть' : 'Свернуть' }}</span>
    </div>
    <div
      :style="{
        height: isCollapsed ? '0' : `${editorHeight}px`,
        overflow: 'hidden',
      }"
      class="editor-container"
    >
      <v-ace-editor
        v-model:value="internalValue"
        :lang="language"
        :options="editorOptions"
        :small="small"
        :theme="lightTheme ? 'xcode' : 'tomorrow_night'"
        class="ace-editor"
        @change="handleChange"
        @init="handleEditorInit"
      />
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseCodeEditor',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { VAceEditor } from 'vue3-ace-editor';
import type { Ace } from 'ace-builds';

import 'ace-builds/src-noconflict/theme-tomorrow_night.js';
import 'ace-builds/src-noconflict/theme-xcode.js';
import 'ace-builds/src-noconflict/ext-language_tools';
import 'ace-builds/src-noconflict/mode-plain_text';
import 'ace-builds/src-noconflict/mode-html';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-css';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/snippets/plain_text';
import 'ace-builds/src-noconflict/snippets/html';
import 'ace-builds/src-noconflict/snippets/javascript';
import 'ace-builds/src-noconflict/snippets/css';
import 'ace-builds/src-noconflict/snippets/python';
import 'ace-builds/src-noconflict/snippets/json';

/**
 * Интерфейс для определения пропсов компонента редактора.
 * @interface Props
 * @property {string} label - Метка для редактора, отображаемая в заголовке.
 * @property {'plain_text' | 'html' | 'javascript' | 'css' | 'python' | 'json'} language - Язык для выделения синтаксиса в редакторе.
 * @property {boolean} isCollapsed - Указывает, свернут редактор или нет. Используется для управления отображением.
 * @property {boolean} isResizable - Указывает, возможно ли изменение размера редактора.
 * @property {number} defaultHeight - Высота редактора по умолчанию. Используется для определения начальной высоты.
 */
interface Props {
  label: string;
  labelColor?: string;
  language: 'plain_text' | 'html' | 'javascript' | 'css' | 'python' | 'json';
  isCollapsed: boolean;
  isResizable: boolean;
  defaultHeight: number;
  lightTheme?: boolean;
  small?: boolean;
  autoHeight?: boolean;
  maxHeight?: number;
  readonly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  autoHeight: false,
  maxHeight: 250,
  readonly: false,
});
const model = defineModel<string | null>({ default: '' });
const aceEditor = ref<Ace.Editor | null>(null);

/**
 * Определяет эмитируемые события компонента.
 * @typedef {Object} Emit
 * @property {function} update:modelValue - Эмитится, когда содержимое редактора изменяется.
 * @property {function} toggle - Эмитится при запросе на переключение состояния редактора (свернуть/развернуть).
 */
const emit = defineEmits<{
  (e: 'toggle'): void;
  (e: 'input'): void;
}>();

const internalValue = computed({
  get: () => model.value ?? '', // Если model.value === null, возвращаем пустую строку
  set: (value) => {
    model.value = value;
  },
});

// Опции для редактора
const editorOptions = computed(() => ({
  enableBasicAutocompletion: !props.readonly,
  enableLiveAutocompletion: !props.readonly,
  enableSnippets: !props.readonly,
  wrap: true,
  readOnly: props.readonly,
}));

// Реактивное состояние для состояния сворачивания
const isCollapsed = ref<boolean>(props.isCollapsed);
const editorHeight = ref<number>(props.defaultHeight);

// Наблюдение за изменениями свойства isCollapsed
watch(
  () => props.isCollapsed,
  (newVal) => {
    isCollapsed.value = newVal;
    if (!newVal) {
      editorHeight.value = props.defaultHeight; // Восстанавливаем высоту при разворачивании
    }
  }
);

/**
 * Переключает состояние редактора. Вызывает эмит события, если редактор изменяемый.
 */
const toggle = () => {
  if (props.isResizable) {
    isCollapsed.value = !isCollapsed.value;
    emit('toggle');
    if (!isCollapsed.value) {
      // Устанавливаем высоту по умолчанию при разворачивании
      editorHeight.value = props.defaultHeight;
    }
  }
};

const updateEditorHeight = () => {
  if (!props.autoHeight || !aceEditor.value || isCollapsed.value) return;

  const renderer = aceEditor.value.renderer;
  const session = aceEditor.value.session;

  const lineHeight = renderer.lineHeight;
  const numberOfLines = session.getLength();

  let newHeight = numberOfLines * lineHeight + 2;

  if (renderer.scrollBarH?.visible) {
    newHeight += renderer.scrollBarH.getHeight();
  }

  if (props.maxHeight && newHeight > props.maxHeight) {
    newHeight = props.maxHeight;
  }

  const minHeight = Math.min(props.defaultHeight, props.maxHeight || Infinity);
  if (newHeight < minHeight) {
    newHeight = minHeight;
  }

  editorHeight.value = newHeight;
};

const handleEditorInit = (editor: Ace.Editor) => {
  aceEditor.value = editor;
  if (props.autoHeight) {
    editor.on('change', updateEditorHeight);
    updateEditorHeight();
  }
};

const handleChange = () => {
  emit('input');
  if (props.autoHeight) {
    updateEditorHeight();
  }
};

onMounted(() => {
  if (props.autoHeight && !isCollapsed.value) {
    updateEditorHeight();
  }
});
</script>

<style scoped>
.resizable-editor {
  display: grid;
  gap: 10px;
  width: 100%;
}

.label-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.label-area.resizable {
  cursor: pointer;
}

.label-text {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.2;
  color: #fff;
}

.label-flag {
  font-size: 12px;
  font-weight: 400;
  color: #8b8b8b;
}

.editor-container {
  position: relative;
  resize: vertical;
  overflow: hidden;
  border: 1px solid #212121;
  border-radius: 8px;
  transition: height 0.2s linear;
}

.collapsed .editor-container {
  height: 0;
  border: none;
  border-bottom: 1px solid #747474;
}

.ace-editor {
  width: 100%;
  height: 100%;
  font-size: 16px;
  line-height: 1.3;
}

/* Задание семейства шрифтов для Ace редактора, без этого положение курсора работает некорректно */
.ace-editor * {
  font-family: monospace !important;
}
</style>

<style>
.ace-editor[small='true'] .ace_gutter-cell {
  padding-left: 3px !important;
  padding-right: 2px !important;
}

.ace-editor[small='true'] {
  font-size: 12px !important;
}
</style>
