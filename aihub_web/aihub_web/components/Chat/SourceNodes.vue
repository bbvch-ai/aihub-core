<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="(documentNodes, doc) in nodesByDocument"
      :key="doc"
      class="relative rounded-3xl border border-surface-100 bg-white p-9 dark:border-surface-600 dark:bg-surface-800"
    >
      <KnowledgeNodeContent
        v-for="node in documentNodes"
        :key="node.id"
        :node="node"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IngestedNode } from '@core/sdk/client'

const props = defineProps<{
  nodes: IngestedNode[]
}>()

const nodesByDocument = computed<Record<string, IngestedNode[]>>(() => {
  const nodeMap: Record<string, IngestedNode[]> = {}
  props.nodes.forEach((node: IngestedNode) => {
    if (!(node.document_id in nodeMap)) {
      nodeMap[node.document_id] = []
    }
    nodeMap[node.document_id].push(node)
  })
  return nodeMap
})
</script>
