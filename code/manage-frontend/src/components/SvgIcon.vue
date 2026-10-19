<template>
  <svg
    :style="{ width: sizeVal, height: sizeVal, color: color }"
    class="svg-icon"
    v-bind="$attrs"
  >
    <title v-if="title">{{ title }}</title>
    <use :href="`#icon-${name}`" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  name: string
  color?: string
  size?: number | string
  title?: string
}>(), {
  size: 16,
})

const sizeVal = computed(() => {
  const s = props.size
  return typeof s === 'number' ? `${s}px` : s
})
</script>

<style scoped>
.svg-icon {
  display: inline-block;
  vertical-align: middle;
  fill: currentColor;
  overflow: hidden;
}
</style>
