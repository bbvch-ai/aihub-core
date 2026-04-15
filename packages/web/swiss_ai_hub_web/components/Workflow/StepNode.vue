<template>
  <WorkflowNodeCard
    :icon="data.icon ?? 'mingcute:ai-fill'"
    :label="data.label"
    :description="data.description"
  />
  <Handle
    type="target"
    :position="Position.Top"
  />
  <Handle
    type="source"
    :position="Position.Bottom"
    :connectable="false"
  />
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

import type { NodeData } from '@core/sdk/client'

defineProps<{
  id: string
  data: NodeData
}>()
</script>
