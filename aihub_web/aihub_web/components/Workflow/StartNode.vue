<template>
  <Handle
    type="target"
    :position="Position.Left"
  />
  <div class="bg-red-500 text-white rounded-md shadow-md border border-stone-100 overflow-hidden p-6 text-lg font-bold">
    {{ props.id }}
  </div>
  <Handle
    type="source"
    :position="Position.Right"
  />
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { NodeData } from '@core/sdk/client'

const props = defineProps<{
  id: string
  data: NodeData
}>()
</script>
