import { createAgent, type CreateAgentRequest } from '@core/sdk/client'

export const useCreateAgent = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: createAgentMutation,
    isPending: isCreating,
    error: createError,
  } = useMutation({
    mutation: async ({ request }: { request: CreateAgentRequest }) => {
      const result = await createAgent({
        composable: '$fetch',
        body: request,
      })

      // Invalidate agents cache to refresh the list
      queryCache.invalidateQueries({ key: ['agents'] })
      return result
    },
  })

  return {
    createAgent: createAgentMutation,
    isCreating,
    createError,
  }
})
