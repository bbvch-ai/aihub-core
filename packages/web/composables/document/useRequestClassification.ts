import { requestClassification } from '@core/sdk/client'

export const useRequestClassification = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  return useMutation({
    mutation: (params: { database: string, tenantId: string }) =>
      requestClassification({
        composable: '$fetch',
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
