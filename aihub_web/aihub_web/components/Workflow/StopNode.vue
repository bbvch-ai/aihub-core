<template>
  <Handle
    type="target"
    :position="Position.Left"
  />
  <div class="overflow-hidden rounded-md border border-surface-100 bg-red-500 p-6 text-lg font-bold text-white shadow-md">
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
