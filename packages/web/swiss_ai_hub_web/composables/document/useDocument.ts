import { type DocumentDto, getDocumentById } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useDocument = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()
  const isRouteReady = useRouteReady('db', 'namespace', 'document_id')

  const { data: document, isPending: documentIsLoading } = useQuery<DocumentDto>({
    key: () => ['knowledge', tenantId.value, 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', route.params.document_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantId.value),
    query: async () => {
      return await getDocumentById({
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
    document,
    documentIsLoading,
  }
})
