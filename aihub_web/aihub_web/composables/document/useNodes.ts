import { getNodesForDocument, type Node } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useNodes = defineQuery(() => {
  const route = useRoute()
  const { data: nodes, isPending: nodesAreLoading } = useQuery<Node[]>({
    key: () => ['knowledge', 'db', route.params.db as string, 'namespace', route.params.namespace as string, 'document', route.params.document_id as string, 'nodes'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getNodesForDocument({
        composable: '$fetch',
        path: {
          db: route.params.db,
          namespace: route.params.namespace,
          document_id: route.params.document_id as string,
        },
      })
    },
  })
  return {
    nodes,
    nodesAreLoading,
  }
})
