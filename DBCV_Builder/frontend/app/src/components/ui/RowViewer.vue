<template>
  <template v-if="isObjectOrArray(val)">
    <tr>
      <td :style="{ paddingLeft: `${depth * 60}px` }" class="custom-table-cell expanded-key">
        <button @click="toggle" class="toggle-button">
          {{ expanded ? '−' : '+' }}
        </button>
        {{ k }}
      </td>
      <td class="custom-table-cell expanded-value">
        {{ Array.isArray(val) ? '[Array]' : '{Object}' }}
      </td>
    </tr>
    <template v-if="expanded">
      <RowViewer
        v-for="(v, subKey) in val"
        :key="`${depth}-${k}-${subKey}`"
        :k="formatKey(subKey)"
        :val="v"
        :depth="depth + 1"
      />
    </template>
  </template>

  <template v-else>
    <tr>
      <td :style="{ paddingLeft: `${depth * 60}px` }" class="custom-table-cell simple-key">
        {{ k }}
      </td>
      <td class="custom-table-cell simple-value">
        {{ val }}
      </td>
    </tr>
  </template>
</template>

<script setup>
import { ref } from 'vue';
import RowViewer from '@/components/ui/RowViewer.vue';

const props = defineProps({
  k: { type: [String, Number], required: true },
  val: { type: [Object, Array, String, Number, Boolean, null], required: true },
  depth: { type: Number, required: true },
});

const expanded = ref(false);

const toggle = () => {
  expanded.value = !expanded.value;
};

const isObjectOrArray = (value) => value !== null && typeof value === 'object';

const formatKey = (key) => (typeof key === 'number' ? `[${key}]` : key);
</script>

<style>
.custom-table-cell {
  padding-top: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgb(93, 93, 93);
  vertical-align: top;
  font-family: monospace;
  white-space: nowrap;
}

.expanded-key {
  color: #3b82f6;
  font-family: monospace;
}

.expanded-value {
  color: #1f2937;
  font-style: italic;
}

.toggle-button {
  color: #3b82f6;
}

.toggle-button:hover {
  text-decoration: underline;
}

.simple-key {
  color: #fff;
  font-family: monospace;
}

.simple-value {
  /* color: #9ca3af; */
  color: #fff;
  word-break: break-word;
}
</style>
