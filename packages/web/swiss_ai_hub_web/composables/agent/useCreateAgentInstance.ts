import { createAgentInstance, type CreateAgentInstanceRequest } from '@core/sdk/client'

export const useCreateAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: createAgentInstanceMutation,
    isPending: isCreating,
    error: createError,
  } = useMutation({
    mutation: async ({ agentClass, request }: { agentClass: string, request: CreateAgentInstanceRequest }) => {
      const result = await createAgentInstance({
        composable: '$fetch',
        path: {
          agent_class: agentClass,
        },
        body: request,
      })

      // Invalidate agent instances cache to refresh the list
      queryCache.invalidateQueries({ key: ['agent-instances'] })
      queryCache.invalidateQueries({ key: ['agent-class-instances', agentClass] })
      return result
    },
  })

  return {
    createAgentInstance: createAgentInstanceMutation,
    isCreating,
    createError,
  }
})
