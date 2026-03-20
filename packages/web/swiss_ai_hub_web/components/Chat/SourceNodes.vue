<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center gap-6 text-sm text-surface-600 dark:text-surface-400">
      <div class="flex items-center gap-2">
        <Icon
          name="mage:file"
          class="size-4"
        />
        <span>{{ t('event.retriever.sourceDocument', documentCount) }}</span>
      </div>
      <div class="flex items-center gap-2">
        <Icon
          name="mage:checklist"
          class="size-4"
        />
        <span>{{ t('event.retriever.contentChunk', totalNodeCount) }}</span>
      </div>
    </div>

    <div
      v-if="totalNodeCount === 0"
      class="flex flex-col items-center gap-3 rounded-lg p-8 text-center"
    >
      <Icon
        name="mage:cancel"
        class="size-8 text-surface-400"
      />
      <div>
        <p class="font-medium text-surface-700 dark:text-surface-300">
          {{ t('event.retriever.noChunksFound') }}
        </p>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          {{ t('event.retriever.noChunksFoundDescription') }}
        </p>
      </div>
    </div>

    <div
      v-else
      class="flex flex-col gap-3"
    >
      <div
        v-for="(documentNodes, doc) in nodesByDocument"
        :key="doc"
        class="rounded-lg border border-surface-200 dark:border-surface-700"
      >
        <div
          v-if="getDocumentTitle(documentNodes)"
          class="flex items-center justify-between border-b border-surface-100 px-4 py-3 dark:border-surface-700"
        >
          <div class="flex items-center gap-2">
            <Icon
              name="mage:file"
              class="size-4 text-surface-500"
            />
            <h3 class="font-medium text-surface-700 dark:text-surface-300">
              {{ getDocumentTitle(documentNodes) }}
            </h3>
          </div>
          <span class="text-xs text-surface-500 dark:text-surface-400">
            {{ t('event.retriever.chunksFromDoc', documentNodes.length) }}
          </span>
        </div>

        <div class="p-4">
          <div class="flex flex-col gap-3">
            <KnowledgeNodeContent
              v-for="node in documentNodes"
              :key="node.id"
              :node="node"
              :always-show-score="true"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IngestedNode } from '@core/sdk/client'

const props = defineProps<{
  nodes: IngestedNode[]
}>()

const { t } = useI18n()

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

const documentCount = computed(() => {
  return Object.keys(nodesByDocument.value).length
})

const totalNodeCount = computed(() => {
  return props.nodes.length
})

const getDocumentTitle = (nodes: IngestedNode[]): string => {
  const nodeWithTitle = nodes.find(node => node.document_title?.trim())
  if (nodeWithTitle?.document_title) {
    return nodeWithTitle.document_title.trim()
  }

  const nodeWithSource = nodes.find(node => node.source?.trim())
  if (nodeWithSource?.source) {
    return nodeWithSource.source
  }
  return ''
}
</script>
