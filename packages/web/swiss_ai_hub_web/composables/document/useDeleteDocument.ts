import { deleteDocument } from '@core/sdk/client'

export const useDeleteDocument = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteDocumentMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ database, namespace, documentId }: { database: string, namespace: string, documentId: string }) => {
      await deleteDocument({
        composable: '$fetch',
        path: {
          database,
          namespace,
          document_id: documentId,
        },
      })

      queryCache.invalidateQueries({ key: ['knowledge', 'databases', database, 'namespaces', namespace, 'documents'] })
    },
  })

  return {
    deleteDocument: deleteDocumentMutation,
    isDeleting,
    deleteError,
  }
})
