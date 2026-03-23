import { createProcessInstance, type CreateProcessInstanceRequest } from '@core/sdk/client'

export const useCreateProcessInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: createProcessInstanceMutation,
    isPending: isCreating,
    error: createError,
  } = useMutation({
    mutation: async ({ processClass, request }: { processClass: string, request: CreateProcessInstanceRequest }) => {
      const result = await createProcessInstance({
        composable: '$fetch',
        path: {
          process_class: processClass,
        },
        body: request,
      })

      queryCache.invalidateQueries({ key: ['process-instances'] })
      queryCache.invalidateQueries({ key: ['process-class-instances', processClass] })
      return result
    },
  })

  return {
    createProcessInstance: createProcessInstanceMutation,
    isCreating,
    createError,
  }
})
