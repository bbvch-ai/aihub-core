<template>
  <!-- You can use the `BaseEdge` component to create your own custom edge more easily -->
  <BaseEdge
    :id="id"
    :style="style"
    :path="path[0]"
    :marker-end="markerEnd"
  />

  <!-- Use the `EdgeLabelRenderer` to escape the SVG world of edges and render your own custom label in a `<div>` ctx -->
  <EdgeLabelRenderer>
    <div
      :style="{
        transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`,
      }"
      class="absolute overflow-hidden rounded-md border border-dashed border-surface-400 bg-surface-50 px-4 py-2 shadow-md dark:border-surface-400 dark:bg-surface-950"
    >
      {{ data.event_name }}
    </div>
  </EdgeLabelRenderer>
</template>

<script setup lang="ts">
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@vue-flow/core'
import { computed } from 'vue'

import type { EdgeData } from '@core/sdk/client'

const props = defineProps<{
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: string
  targetPosition: string
  data: EdgeData
  markerEnd: string
  style: Record<string, string>
}>()

const path = computed(() => getBezierPath(props))
</script>
