<template>
  <WorkflowNodeCard
    :icon="data.icon ?? 'mage:play-circle-fill'"
    :label="data.label"
    :description="data.description"
    accent="red"
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
