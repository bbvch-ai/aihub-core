import { updateAgentInstance } from '@core/sdk/client'

export const useUpdateAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateAgentInstanceMutation, isPending: isUpdating } = useMutation({
    mutation: async ({
      agentClass,
      agentId,
      tenantId,
      configuration,
    }: {
      agentClass: string
      agentId: string
      tenantId: string
      configuration: Record<string, unknown>
    }) => {
      const result = await updateAgentInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          agent_class: agentClass,
          agent_id: agentId,
        },
        body: {
          configuration,
        },
      })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-instances', agentClass, agentId] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-instances'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-class-instances', agentClass] })
      return result
    },
  })

  return {
    updateAgentInstance: updateAgentInstanceMutation,
    isUpdating,
  }
})
