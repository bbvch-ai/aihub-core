import { deleteNamespace } from '@core/sdk/client'

export const useDeleteNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteNamespaceMutation,
    isLoading: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ tenantId, database, namespace }: { tenantId: string, database: string, namespace: string }) => {
      await deleteNamespace({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          database,
          namespace,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge'] })
    },
  })

  return {
    deleteNamespace: deleteNamespaceMutation,
    isDeleting,
    deleteError,
  }
})
