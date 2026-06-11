import { createTenantMetadata as createTenantMetadataApi, type CreateTenantMetadataRequest } from '~/sdk/client'

export const useCreateTenantMetadata = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: createTenantMetadataMutation } = useMutation({
    mutation: async ({ data }: { data: CreateTenantMetadataRequest }) => {
      await createTenantMetadataApi({
        composable: '$fetch',
        body: data,
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['admin-tenants', 'unconfigured'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    createTenantMetadata: createTenantMetadataMutation,
  }
})
