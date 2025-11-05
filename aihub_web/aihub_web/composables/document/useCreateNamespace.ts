import { createNamespace, type CreateNamespaceRequest } from '@core/sdk/client'

export const useCreateNamespace = defineMutation(() => {
  const queryCache = useQueryCache()

  return useMutation({
    mutation: (request: CreateNamespaceRequest & { database: string, namespace: string }) =>
      createNamespace({
        composable: '$fetch',
        body: {
          folder_name: request.folder_name,
          display_name: request.display_name,
          description: request.description,
        },
        path: {
          database: request.database,
          namespace: request.namespace,
        },
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })
})
