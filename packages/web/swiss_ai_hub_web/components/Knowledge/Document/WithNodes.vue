<template>
  <div
    v-if="!(documentNodesAreLoading || documentIsLoading)"
    class="relative rounded-3xl border border-surface-100 bg-white p-9 dark:border-surface-600 dark:bg-surface-800"
  >
    <KnowledgeDocumentOverview :document="document">
      <div class="mb-4 flex justify-end">
        <Button
          v-if="document?.source"
          icon="pi pi-external-link"
          :label="t('knowledge.original.view_button')"
          size="small"
          variant="outlined"
          @click="openOriginalDocument"
        />
      </div>
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
import { type IngestedDocument, getDocumentById, getNodesForDocument, type IngestedNode } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

const props = defineProps<{
  db: string
  namespace: string
  documentId: string
  inputNodes: IngestedNode[]
  showInactive: boolean
}>()

const { t } = useI18n()
const { tenantId } = useTenant()
const { getDocumentSourceUrl } = useDocumentUrl()

const { data: document, isPending: documentIsLoading } = useQuery<IngestedDocument>({
  key: () => ['knowledge', 'db', props.db, 'namespace', props.namespace, 'document', props.documentId as string],
  staleTime: minutesToMilliseconds(5),
  enabled: true,
  query: async () => {
    return await getDocumentById({
      composable: '$fetch',
      path: {
        tenant_id: tenantId.value!,
        database: props.db,
        namespace: props.namespace,
        document_id: props.documentId as string,
      },
    })
  },
})

const { data: documentNodes, isPending: documentNodesAreLoading } = useQuery<Node[]>({
  key: () => ['knowledge', 'db', props.db, 'namespace', props.namespace, 'document', props.documentId, 'nodes'],
  staleTime: minutesToMilliseconds(5),
  enabled: true,
  query: async () => {
    return await getNodesForDocument({
      composable: '$fetch',
      path: {
        tenant_id: tenantId.value!,
        database: props.db,
        namespace: props.namespace,
        document_id: props.documentId as string,
      },
    })
  },
})

const openOriginalDocument = async () => {
  if (!document.value?.source) return

  try {
    const url = await getDocumentSourceUrl(props.db, props.namespace, props.documentId)
    window.open(url, '_blank')
  }
  catch (e) {
    console.error('Error opening document:', e)
  }
}

const combinedNodes = computed<{ node: IngestedNode, isActive: boolean }[]>(() => {
  const combNodes: { node: IngestedNode, isActive: boolean }[] = [];
  (documentNodes.value ?? []).forEach((node: IngestedNode) => {
    const activeNode = props.inputNodes.find((n: IngestedNode) => n.id === node.id)
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
