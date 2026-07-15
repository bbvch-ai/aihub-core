import { createDatabase, type CreateDatabaseRequest } from '@core/sdk/client'

export const useCreateDatabase = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  return useMutation({
    mutation: (request: CreateDatabaseRequest & { database: string, tenantId: string }) =>
      createDatabase({
        composable: '$fetch',
        body: {
          display_name: request.display_name,
          description: request.description,
          ingestor: request.ingestor,
        },
        path: {
          tenant_id: request.tenantId,
          database: request.database,
        },
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'knowledge'] })
    },
  })
})
