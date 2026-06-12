import type { BatchDeleteDocumentsResponse } from '@core/sdk/client'
import { batchDeleteDocuments } from '@core/sdk/client'

export const useDeleteDocuments = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteDocumentsMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ tenantId, database, namespace, documentIds }: { tenantId: string, database: string, namespace: string, documentIds: string[] }): Promise<BatchDeleteDocumentsResponse> => {
      const response = await batchDeleteDocuments({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          database,
          namespace,
        },
        body: {
          document_ids: documentIds,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge', 'databases', database, 'namespaces', namespace, 'documents'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge', 'databases'] })

      return response
    },
  })

  return {
    deleteDocuments: deleteDocumentsMutation,
    isDeleting,
    deleteError,
  }
})
