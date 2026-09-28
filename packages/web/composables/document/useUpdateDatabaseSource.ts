import { updateDatabaseSource, type UpdateDatabaseSourceRequest } from '@core/sdk/client'

export const useUpdateDatabaseSource = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  return useMutation({
    mutation: (params: { database: string, tenantId: string, request: UpdateDatabaseSourceRequest }) =>
      updateDatabaseSource({
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
