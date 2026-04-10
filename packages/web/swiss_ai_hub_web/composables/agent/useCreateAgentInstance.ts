import { createAgentInstance, type CreateAgentInstanceRequest } from '@core/sdk/client'

export const useCreateAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: createAgentInstanceMutation,
    isPending: isCreating,
    error: createError,
  } = useMutation({
    mutation: async ({ agentClass, request, tenantId }: { agentClass: string, request: CreateAgentInstanceRequest, tenantId: string }) => {
      const result = await createAgentInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          agent_class: agentClass,
        },
        body: request,
      })

      // Invalidate agent instances cache to refresh the list
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-instances'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-class-instances', agentClass] })
      return result
    },
  })

  return {
    createAgentInstance: createAgentInstanceMutation,
    isCreating,
    createError,
  }
})
