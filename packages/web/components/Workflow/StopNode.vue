<template>
  <WorkflowNodeCard
    :icon="data.icon ?? 'mage:stop-circle-fill'"
    :label="data.label"
    :description="data.description"
    accent="red"
  />
  <Handle
    type="target"
    :position="Position.Top"
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
