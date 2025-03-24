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
      class="absolute px-4 py-2 bg-stone-50 dark:bg-stone-950 rounded-md shadow-md border border-dashed border-stone-400 dark:border-stone-400 overflow-hidden"
    >
      {{ data.event_type }}
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
