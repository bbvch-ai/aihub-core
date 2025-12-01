import { deleteMemory, deleteAllMemories } from '@core/sdk/client'

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

export const useDeleteAllMemories = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: deleteAllMemoriesMutation } = useMutation({
    mutation: async () => {
      await deleteAllMemories({
        composable: '$fetch',
      })
      queryCache.invalidateQueries({ key: ['memories'] })
      queryCache.invalidateQueries({ key: ['memory-search'] })
    },
  })

  return {
    deleteAllMemories: deleteAllMemoriesMutation,
  }
})
