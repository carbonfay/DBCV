<script lang="ts" setup>
import { computed } from 'vue';
import { BaseEdge, type EdgeProps } from '@vue-flow/core';

const props = defineProps<EdgeProps>();

function getBezierPath({
  sourceX,
  sourceY,
  targetX,
  targetY,
  curvature = 0.5,
}: {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  curvature?: number;
}): [string, number, number] {
  let cX = Math.abs(targetX - sourceX) * curvature;
  if (cX < 100) cX = 100 * curvature;

  let cY = targetY - sourceY;
  if (sourceX > targetX && Math.abs(cY) < 100 && sourceX - targetX > 250)
    cY = 100 * curvature * (cY < 0 ? 1 : -1);
  else cY = 0;

  const c1 = { x: sourceX + cX, y: sourceY + cY };
  const c2 = { x: targetX - cX, y: targetY + cY };
  const path = `M${sourceX},${sourceY} C${c1.x},${c1.y} ${c2.x},${c2.y} ${targetX},${targetY}`;
  const labelX = (sourceX + targetX) / 2;
  const labelY = (sourceY + targetY) / 2;
  return [path, labelX, labelY];
}

const edgePathParams = computed(() =>
  getBezierPath({
    ...props,
    sourceX: props.sourceX,
    targetX: props.targetX,
    curvature: 0.7,
  })
);

const path = computed(() => edgePathParams.value[0]);

// TODO: Animation

// const animation = ref<JSAnimation>();
// const obj = useTemplateRef('object');

// function recalculateAnimation() {
//   const el = document.createElementNS('http://www.w3.org/2000/svg', 'path');
//   el.setAttribute('d', path.value);
//   const edgePathLength = el.getTotalLength();
//   const speed = 0.5;
//   const duration = edgePathLength / speed;
//
//   if (!obj.value) return;
//   animation.value = animate(obj.value, {
//     ease: 'linear',
//     delay: 100,
//     duration,
//     autoplay: false,
//     ...svg.createMotionPath(el),
//   });
// }
//
// watch(path, () => {
//   recalculateAnimation();
// });

// defineExpose({ animation, recalculateAnimation });
</script>

<template>
  <BaseEdge :path="path" v-bind="props" />
  <!--  <rect ref="object" height="16" rx="5" ry="5" width="20" x="-10" y="-8" />-->
</template>

<style scoped></style>
