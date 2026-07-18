import { deleteDocument } from '@core/sdk/client'

export const useDeleteDocument = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteDocumentMutation,
    isLoading: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ tenantId, database, namespace, documentId }: { tenantId: string, database: string, namespace: string, documentId: string }) => {
      await deleteDocument({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          database,
          namespace,
          document_id: documentId,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge', 'databases', database, 'namespaces', namespace, 'documents'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge', 'databases'] })
    },
  })

  return {
    deleteDocument: deleteDocumentMutation,
    isDeleting,
    deleteError,
  }
})
