import { getNodesForDocument, type IngestedNode } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useNodes = defineQuery(() => {
  const route = useRoute()
  const { tenantName } = useTenantFromRoute()
  const isRouteReady = useRouteReady('db', 'namespace', 'document_id')

  const { data: nodes, isPending: nodesAreLoading } = useQuery<IngestedNode[]>({
    key: () => ['knowledge', tenantName.value, 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', route.params.document_id as string, 'nodes'],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantName.value),
    query: async () => {
      return await getNodesForDocument({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
