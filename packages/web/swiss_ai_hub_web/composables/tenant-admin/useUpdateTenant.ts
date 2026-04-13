import { updateTenant as updateTenantApi, type UpdateTenantRequest } from '@core/sdk/client'

export const useUpdateTenant = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateTenantMutation } = useMutation({
    mutation: async ({ tenantId, data }: { tenantId: string, data: UpdateTenantRequest }) => {
      await updateTenantApi({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: data,
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    updateTenant: updateTenantMutation,
  }
})
