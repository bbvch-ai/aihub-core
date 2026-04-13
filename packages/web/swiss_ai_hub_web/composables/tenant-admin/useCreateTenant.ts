import { createTenant as createTenantApi, type CreateTenantRequest } from '@core/sdk/client'

export const useCreateTenant = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: createTenantMutation } = useMutation({
    mutation: async ({ data }: { data: CreateTenantRequest }) => {
      await createTenantApi({
        composable: '$fetch',
        body: data,
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    createTenant: createTenantMutation,
  }
})
