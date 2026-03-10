import { updateProcessInstance } from '@core/sdk/client'

export const useUpdateProcessInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateProcessInstanceMutation, isPending: isUpdating } = useMutation({
    mutation: async ({
      processClass,
      processId,
      configuration,
    }: {
      processClass: string
      processId: string
      configuration: Record<string, unknown>
    }) => {
      const result = await updateProcessInstance({
        composable: '$fetch',
        path: {
          process_class: processClass,
          process_id: processId,
        },
        body: {
          configuration,
        },
      })
      queryCache.invalidateQueries({ key: ['process-instances', processClass, processId] })
      queryCache.invalidateQueries({ key: ['process-instances'] })
      queryCache.invalidateQueries({ key: ['process-class-instances', processClass] })
      return result
    },
  })

  return {
    updateProcessInstance: updateProcessInstanceMutation,
    isUpdating,
  }
})
