import { configureTenant as configureTenantApi, type ConfigureTenantRequest } from '@core/sdk/client'

export const useConfigureTenant = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: configureTenantMutation } = useMutation({
    mutation: async ({ data }: { data: ConfigureTenantRequest }) => {
      await configureTenantApi({
        composable: '$fetch',
        body: data,
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['admin-tenants', 'unconfigured'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    configureTenant: configureTenantMutation,
  }
})
