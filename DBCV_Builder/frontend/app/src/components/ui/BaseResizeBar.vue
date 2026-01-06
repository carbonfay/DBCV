<template>
  <div>
    <div class="resize-box">
      <div class="resize-bar" @mousedown="onMouseDown" />
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BaseResizeBar',
  inheritAttrs: true,
  customOptions: {},
};
</script>

<script setup lang="ts">
import { computed, ref } from 'vue';

interface Props {
  position?: 'left' | 'right';
  min?: number;
  max?: number;
  initValue?: number;
}

const props = withDefaults(defineProps<Props>(), {
  position: 'right',
  min: 50,
  max: 800,
  initValue: 200,
});

const currentWidth = ref(props.initValue);

const slide = (e: MouseEvent) => {
  if (props.position === 'right') currentWidth.value += e.movementX;
  if (props.position === 'left') currentWidth.value -= e.movementX;

  if (currentWidth.value <= props.min) {
    currentWidth.value = props.min;
  } else if (currentWidth.value >= props.max) {
    currentWidth.value = props.max;
  }
};

const onMouseDown = (e: MouseEvent) => {
  e.preventDefault();
  document.addEventListener('mousemove', slide);
  document.addEventListener('mouseup', () => document.removeEventListener('mousemove', slide));
};

const width = computed(() => currentWidth.value + 'px');

defineExpose({
  width,
});
</script>

<style scoped>
.resize-box {
  float: v-bind(position);
}

.resize-bar {
  width: 5px;
  height: 100%;
  cursor: ew-resize;
  background-color: #2a2a2a;
  transition: 150ms ease-in-out;
  position: absolute;
  z-index: 1;
}

.resize-bar:hover {
  background: #575757;
}
</style>
