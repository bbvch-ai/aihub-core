import { createNamespace, type CreateNamespaceRequest } from '@core/sdk/client'

export const useCreateNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  return useMutation({
    mutation: (request: Ref<CreateNamespaceRequest>) =>
      createNamespace({
        composable: '$fetch',
        body: request,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })
})
