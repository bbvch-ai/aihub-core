import { deleteMemory } from '@core/sdk/client'

export const useDeleteMemory = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: deleteMemoryMutation } = useMutation({
    mutation: async ({ memoryId }: { memoryId: string }) => {
      await deleteMemory({
        composable: '$fetch',
        path: {
          memory_id: memoryId,
        },
      })
      queryCache.invalidateQueries({ key: ['memories'] })
    },
  })

  return {
    deleteMemory: deleteMemoryMutation,
  }
})
