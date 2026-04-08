import { getNodesForDocument, type IngestedNode } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useNodes = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: nodes, isPending: nodesAreLoading } = useQuery<IngestedNode[]>({
    key: () => ['tenant', tenantId.value, 'knowledge', 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', route.params.document_id as string, 'nodes'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('db', 'namespace', 'document_id'),
    query: async () => {
      return await getNodesForDocument({
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
    nodes,
    nodesAreLoading,
  }
})
