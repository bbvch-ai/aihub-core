import { createDatabase, type CreateDatabaseRequest } from '@core/sdk/client'

export const useCreateDatabase = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  return useMutation({
    mutation: (params: { database: string, tenantId: string, request: CreateDatabaseRequest }) =>
      createDatabase({
        composable: '$fetch',
        body: params.request,
        path: {
          tenant_id: params.tenantId,
          database: params.database,
        },
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'knowledge'] })
    },
  })
})
