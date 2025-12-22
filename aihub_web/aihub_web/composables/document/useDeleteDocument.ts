export const useDeleteDocument = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: deleteDocumentMutation, isPending } = useMutation({
    mutation: async (params: { database: string, namespace: string, documentId: string }) => {
      return await $fetch<{ success: boolean }>(
        `/api/knowledge/databases/${encodeURIComponent(params.database)}/namespaces/${encodeURIComponent(params.namespace)}/documents/${encodeURIComponent(params.documentId)}`,
        {
          method: 'DELETE',
        },
      )
    },
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })

  return {
    deleteDocument: deleteDocumentMutation,
    isPending,
  }
})
