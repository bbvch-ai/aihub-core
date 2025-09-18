<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-4 rounded-lg bg-surface-50 p-3 dark:bg-surface-800/50">
      <div class="flex items-center gap-2">
        <Icon
          name="material-symbols:article-outline"
          class="size-4 text-surface-500"
        />
        <span class="text-sm text-surface-600 dark:text-surface-400">
          {{ documentCount }} {{ documentCount === 1 ? 'source document' : 'source documents' }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <Icon
          name="material-symbols:view-agenda-outline"
          class="size-4 text-surface-500"
        />
        <span class="text-sm text-surface-600 dark:text-surface-400">
          {{ totalNodeCount }} {{ totalNodeCount === 1 ? 'content chunk' : 'content chunks' }}
        </span>
      </div>
      <div
        v-if="averageScore > 0"
        class="flex items-center gap-2"
      >
        <Icon
          name="material-symbols:percent"
          class="size-4 text-surface-500"
        />
        <span class="text-sm text-surface-600 dark:text-surface-400">
          {{ Math.round(averageScore * 100) }}% avg relevance
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="totalNodeCount === 0"
      class="flex flex-col items-center gap-3 rounded-2xl border border-surface-200 bg-white p-12 text-center dark:border-surface-700 dark:bg-surface-800"
    >
      <Icon
        name="material-symbols:search-off"
        class="size-12 text-surface-400"
      />
      <h3 class="font-semibold text-surface-700 dark:text-surface-300">
        No chunks found
      </h3>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        The retrieval search didn't find any relevant content chunks.
      </p>
    </div>

    <!-- Document Sections -->
    <div
      v-else
      class="flex flex-col gap-4"
    >
      <div
        v-for="(documentNodes, doc) in nodesByDocument"
        :key="doc"
        class="relative rounded-2xl border border-surface-200 bg-white shadow-sm dark:border-surface-700 dark:bg-surface-800"
      >
        <div
          v-if="getDocumentTitle(documentNodes)"
          class="flex items-center justify-between border-b border-surface-100 px-6 py-4 dark:border-surface-700"
        >
          <div class="flex items-center gap-3">
            <Icon
              name="material-symbols:article-outline"
              class="size-5 text-surface-500"
            />
            <h3 class="font-semibold text-surface-700 dark:text-surface-300">
              {{ getDocumentTitle(documentNodes) }}
            </h3>
          </div>
          <Tag
            :value="t('event.retriever.chunksFromDoc', { count: documentNodes.length })"
            severity="info"
            class="text-xs"
          />
        </div>

        <div class="p-6">
          <div class="flex flex-col gap-4">
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

// Statistics computed properties
const documentCount = computed(() => {
  return Object.keys(nodesByDocument.value).length
})

const totalNodeCount = computed(() => {
  return props.nodes.length
})

const averageScore = computed(() => {
  const scoresWithValues = props.nodes
    .map(node => node.score)
    .filter((score): score is number => score !== undefined && score !== null)

  if (scoresWithValues.length === 0) return 0

  const sum = scoresWithValues.reduce((acc, score) => acc + score, 0)
  return sum / scoresWithValues.length
})

const getDocumentTitle = (nodes: IngestedNode[]): string | null => {
  // Get title from the first node that has one, or fallback to source filename
  const nodeWithTitle = nodes.find(node => node.document_title)
  if (nodeWithTitle?.document_title) {
    return nodeWithTitle.document_title
  }

  // Fallback to filename from source if no title available
  const firstNode = nodes[0]
  if (firstNode?.source) {
    const filename = firstNode.source.split('/').pop() || firstNode.source
    return filename
  }

  return null
}
</script>
