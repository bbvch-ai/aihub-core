import { updateMemory, type UpdateMemoryRequest } from '@core/sdk/client'

export const useUpdateMemory = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateMemoryMutation } = useMutation({
    mutation: async ({ memoryId, data }: { memoryId: string, data: string }) => {
      await updateMemory({
        composable: '$fetch',
        path: {
          memory_id: memoryId,
        },
        body: {
          data,
        } as UpdateMemoryRequest,
      })
      queryCache.invalidateQueries({ key: ['memories'] })
    },
  })

  return {
    updateMemory: updateMemoryMutation,
  }
})
