<template>
  <div
    v-if="!(documentNodesAreLoading || documentIsLoading)"
    class="relative rounded-3xl border border-surface-100 bg-white p-9 dark:border-surface-600 dark:bg-surface-800"
  >
    <KnowledgeDocumentOverview :document="document">
      <KnowledgeNodeContent
        v-for="node in combinedNodes"
        :key="node.node.id"
        always-show-score
        :node="node.node"
        :active="node.isActive"
      />
    </KnowledgeDocumentOverview>
  </div>
</template>

<script setup lang="ts">
import { type DocumentDto, getDocumentById, getNodesForDocument, type Node } from '@core/sdk/client'

const props = defineProps<{
  db: string
  namespace: string
  documentId: string
  inputNodes: Node[]
  showInactive: boolean
}>()

const { data: document, isPending: documentIsLoading } = useQuery<DocumentDto>({
  key: () => ['knowledge', 'db', props.db, 'namespace', props.namespace, 'document', props.documentId as string],
  staleTime: 1000 * 60 * 5, // 5 minutes
  enabled: true,
  query: async () => {
    return await getDocumentById({
      composable: '$fetch',
      path: {
        db: props.db,
        namespace: props.namespace,
        document_id: props.documentId as string,
      },
    })
  },
})

const { data: documentNodes, isPending: documentNodesAreLoading } = useQuery<Node[]>({
  key: () => ['knowledge', 'db', props.db, 'namespace', props.namespace, 'document', props.documentId, 'nodes'],
  staleTime: 1000 * 60 * 5,
  enabled: true,
  query: async () => {
    return await getNodesForDocument({
      composable: '$fetch',
      path: {
        db: props.db,
        namespace: props.namespace,
        document_id: props.documentId as string,
      },
    })
  },
})

const combinedNodes = computed<{ node: Node, isActive: boolean }[]>(() => {
  const combNodes: { node: Node, isActive: boolean }[] = [];
  (documentNodes.value ?? []).forEach((node: Node) => {
    const activeNode = props.inputNodes.find((n: Node) => n.id === node.id)
    if (activeNode) {
      combNodes.push({ node: activeNode, isActive: true })
    }
    else if (props.showInactive) {
      combNodes.push({ node, isActive: false })
    }
  })
  return combNodes
})
</script>

<style scoped>

</style>
