import { updateNamespace, type UpdateNamespaceRequest } from '@core/sdk/client'

export const useUpdateNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  return useMutation({
    mutation: ({ database, namespace, payload }: { database: string, namespace: string, payload: Ref<UpdateNamespaceRequest> }) =>
      updateNamespace({
        composable: '$fetch',
        path: {
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
