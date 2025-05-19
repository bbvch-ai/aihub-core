<template>
  <div
    v-if="!documentNodesAreLoading"
    class="relative rounded-3xl border border-surface-100 bg-white p-9 dark:border-surface-600 dark:bg-surface-800"
  >
    <div class="absolute right-2 top-2 flex items-center gap-2">
      <p class="text-sm opacity-60">
        Show Unused Nodes
      </p>
      <ToggleSwitch
        v-model="showInactive"
      />
    </div>
    <KnowledgeNodeContent
      v-for="node in combinedNodes"
      :key="node.node.id"
      always-show-score
      :node="node.node"
      :active="node.isActive"
    />
  </div>
</template>

<script setup lang="ts">
import { getNodesForDocument, type Node } from '@core/sdk/client'

const props = defineProps<{
  db: string
  namespace: string
  documentId: string
  inputNodes: Node[]
}>()

const showInactive = ref<boolean>(false)

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
    else if (showInactive.value) {
      combNodes.push({ node, isActive: false })
    }
  })
  return combNodes
})
</script>

<style scoped>

</style>
