import { deleteAgentInstance } from '@core/sdk/client'

export const useDeleteAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteAgentInstanceMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ agentClass, agentId, tenantId }: { agentClass: string, agentId: string, tenantId: string }) => {
      await deleteAgentInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          agent_class: agentClass,
          agent_id: agentId,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-instances'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'agent-class-instances', agentClass] })
      // Deleting an instance removes its per-instance admin role, so the tenant roles list and the
      // creator's own account (roles + accessible services) are now stale
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'roles'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'my_user'] })
    },
  })

  return {
    deleteAgentInstance: deleteAgentInstanceMutation,
    isDeleting,
    deleteError,
  }
})
