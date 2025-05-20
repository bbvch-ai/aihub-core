import {
  type DocumentDto,
  getNodesForDocument,
  getSummaryNodesForDocument,
  type Node,
  type NodeSummaryDto,
} from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useSummaryNodes = defineQuery(() => {
  const route = useRoute()
  const { data: summaryNodes, isPending: nodesummaryNodesAreLoading } = useQuery<NodeSummaryDto[]>({
    key: () => ['knowledge', 'db', route.params.db as string, 'namespace', route.params.namespace as string, 'document', route.params.document_id as string, 'summaries'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getSummaryNodesForDocument({
        composable: '$fetch',
        path: {
          db: route.params.db as string,
          namespace: route.params.namespace as string,
          document_id: route.params.document_id as string,
        },
      })
    },
  })
  return {
    summaryNodes,
    nodesummaryNodesAreLoading,
  }
})
