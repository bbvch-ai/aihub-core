import { deleteAgentInstance } from '@core/sdk/client'

export const useDeleteAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteAgentInstanceMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ agentClass, agentId }: { agentClass: string, agentId: string }) => {
      await deleteAgentInstance({
        composable: '$fetch',
        path: {
          agent_class: agentClass,
          agent_id: agentId,
        },
      })

      queryCache.invalidateQueries({ key: ['agent-instances'] })
      queryCache.invalidateQueries({ key: ['agent-class-instances', agentClass] })
    },
  })

  return {
    deleteAgentInstance: deleteAgentInstanceMutation,
    isDeleting,
    deleteError,
  }
})
