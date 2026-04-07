import { updateNamespace, type UpdateNamespaceRequest } from '@core/sdk/client'

export const useUpdateNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  return useMutation({
    mutation: ({ database, namespace, payload, tenantId }: { database: string, namespace: string, payload: Ref<UpdateNamespaceRequest>, tenantId: string }) =>
      updateNamespace({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          database,
          namespace,
        },
        body: payload,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })
})
