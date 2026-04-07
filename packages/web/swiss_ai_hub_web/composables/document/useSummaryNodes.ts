import {
  getSummaryNodesForDocument,
  type NodeSummaryDto,
} from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useSummaryNodes = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: summaryNodes, isPending: summaryNodesAreLoading } = useQuery<NodeSummaryDto[]>({
    key: () => ['tenant', tenantId.value, 'knowledge', 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', route.params.document_id as string, 'summaries'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('db', 'namespace', 'document_id'),
    query: async () => {
      return await getSummaryNodesForDocument({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
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
