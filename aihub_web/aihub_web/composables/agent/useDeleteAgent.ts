import { deleteAgent } from '@core/sdk/client'

export const useDeleteAgent = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteAgentMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ agentClass, agentId }: { agentClass: string, agentId: string }) => {
      await deleteAgent({
        composable: '$fetch',
        path: {
          agent_class: agentClass,
          agent_id: agentId,
        },
      })

      // Invalidate agents cache to refresh the list
      queryCache.invalidateQueries({ key: ['agents'] })
    },
  })

  return {
    deleteAgent: deleteAgentMutation,
    isDeleting,
    deleteError,
  }
})
