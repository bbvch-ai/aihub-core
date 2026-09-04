import { deleteDatabase } from '@core/sdk/client'

export const useDeleteDatabase = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteDatabaseMutation,
    isLoading: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ tenantId, database }: { tenantId: string, database: string }) => {
      await deleteDatabase({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          database,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'knowledge'] })
    },
  })

  return {
    deleteDatabase: deleteDatabaseMutation,
    isDeleting,
    deleteError,
  }
})
