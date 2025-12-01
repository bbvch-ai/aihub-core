import { getNodesForDocument, type IngestedNode } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useNodes = defineQuery(() => {
  const route = useRoute()

  const database = computed(() => route.params.db as string)
  const namespace = computed(() => route.params.namespace as string)
  const documentId = computed(() => route.params.document_id as string)

  const { data: nodes, isPending: nodesAreLoading } = useQuery<IngestedNode[]>({
    key: () => ['knowledge', 'databases', database.value, 'namespaces', namespace.value, 'documents', documentId.value, 'nodes'],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!database.value && !!namespace.value && !!documentId.value,
    query: async () => {
      return await getNodesForDocument({
        composable: '$fetch',
        path: {
          database: database.value,
          namespace: namespace.value,
          document_id: documentId.value,
        },
      })
    },
  })
  return {
    nodes,
    nodesAreLoading,
  }
})
