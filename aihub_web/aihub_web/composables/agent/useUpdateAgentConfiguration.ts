import { updateAgentConfiguration } from '@core/sdk/client'

export const useUpdateAgentConfiguration = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateAgentConfigurationMutation, isPending: isUpdating } = useMutation({
    mutation: async ({
      agentClass,
      agentId,
      configuration,
    }: {
      agentClass: string
      agentId: string
      configuration: Record<string, unknown>
    }) => {
      const result = await updateAgentConfiguration({
        composable: '$fetch',
        path: {
          agent_class: agentClass,
          agent_id: agentId,
        },
        body: {
          configuration,
        },
      })
      // Invalidate the configuration query to refresh the data
      queryCache.invalidateQueries({ key: ['agents', agentClass, agentId, 'configuration'] })
      // Also invalidate the agent query in case config affects agent display
      queryCache.invalidateQueries({ key: ['agents', agentClass, agentId] })
      return result
    },
  })

  return {
    updateAgentConfiguration: updateAgentConfigurationMutation,
    isUpdating,
  }
})
