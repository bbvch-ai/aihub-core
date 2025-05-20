<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="(nodes, doc) in nodesByDocument"
      :key="doc"
      class="relative rounded-3xl border border-surface-100 bg-white p-9 dark:border-surface-600 dark:bg-surface-800"
    >
      <KnowledgeNodeContent
        v-for="node in nodes"
        :key="node.id"
        :node="node"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Document, Node } from '@core/sdk/client'

const props = defineProps<{
  documents: Document[]
}>()

const nodesByDocument = computed<Record<string, Node[]>>(() => {
  const docs: Record<string, Node[]> = {}
  props.documents.forEach((doc: Document) => {
    if (!(doc.metadata.document_id in docs)) {
      docs[doc.metadata.document_id] = []
    }
    docs[doc.metadata.document_id].push(doc.metadata)
  })
  return docs
})
</script>
