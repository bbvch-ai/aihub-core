import {
  getSummaryNodesForDocument,
  type NodeSummaryDto,
} from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useSummaryNodes = defineQuery(() => {
  const route = useRoute()
  const { data: summaryNodes, isPending: summaryNodesAreLoading } = useQuery<NodeSummaryDto[]>({
    key: () => ['knowledge', 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', route.params.document_id as string, 'summaries'],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!route.params.db && route.params.db !== '{db}' && !!route.params.namespace && route.params.namespace !== '{namespace}' && !!route.params.document_id && route.params.document_id !== '{document_id}',
    query: async () => {
      return await getSummaryNodesForDocument({
        composable: '$fetch',
        path: {
          database: route.params.db as string,
          namespace: route.params.namespace as string,
          document_id: route.params.document_id as string,
        },
      })
    },
  })
  return {
    summaryNodes,
    summaryNodesAreLoading,
  }
})
