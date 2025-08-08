import { updateNamespace, type UpdateNamespaceRequest } from '@core/sdk/client'

export const useUpdateNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  return useMutation({
    mutation: ({ id, payload }: { id: string, payload: Ref<UpdateNamespaceRequest> }) =>
      updateNamespace({
        composable: '$fetch',
        path: { namespace_id: id },
        body: payload,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })
})
