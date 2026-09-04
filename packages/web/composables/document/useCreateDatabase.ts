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
          llm_model: request.llm_model,
          embedding_model: request.embedding_model,
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
