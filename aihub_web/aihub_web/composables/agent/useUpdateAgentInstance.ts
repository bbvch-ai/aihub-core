import { updateAgentInstance } from '@core/sdk/client'

export const useUpdateAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateAgentInstanceMutation, isPending: isUpdating } = useMutation({
    mutation: async ({
      agentClass,
      agentId,
      configuration,
    }: {
      agentClass: string
      agentId: string
      configuration: Record<string, unknown>
    }) => {
      const result = await updateAgentInstance({
        composable: '$fetch',
        path: {
          agent_class: agentClass,
          agent_id: agentId,
        },
        body: {
          configuration,
        },
      })
      queryCache.invalidateQueries({ key: ['agent-instances', agentClass, agentId] })
      queryCache.invalidateQueries({ key: ['agent-instances'] })
      queryCache.invalidateQueries({ key: ['agent-class-instances', agentClass] })
      return result
    },
  })

  return {
    updateAgentInstance: updateAgentInstanceMutation,
    isUpdating,
  }
})
