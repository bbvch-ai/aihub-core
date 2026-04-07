import { deleteRole } from '@core/sdk/client'

export const useDeleteRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: removeRole } = useMutation({
    mutation: async ({ roleId, tenantId }: { roleId: string, tenantId: string }) => {
      await deleteRole({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          role_id: roleId,
        },
      })
      queryCache.invalidateQueries({ key: ['roles'] })
    },
  })
  return {
    deleteRole: removeRole,
  }
})
