import { deleteTenant as deleteTenantApi } from '@core/sdk/client'

export const useDeleteTenant = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: deleteTenantMutation } = useMutation({
    mutation: async ({ tenantId }: { tenantId: string }) => {
      await deleteTenantApi({
        composable: '$fetch',
        path: { tenant_id: tenantId },
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    deleteTenant: deleteTenantMutation,
  }
})
