import { updateProcessInstance } from '@core/sdk/client'

export const useUpdateProcessInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateProcessInstanceMutation, isPending: isUpdating } = useMutation({
    mutation: async ({
      processClass,
      processId,
      tenantId,
      configuration,
    }: {
      processClass: string
      processId: string
      tenantId: string
      configuration: Record<string, unknown>
    }) => {
      const result = await updateProcessInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          process_class: processClass,
          process_id: processId,
        },
        body: {
          configuration,
        },
      })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'process-instances', processClass, processId] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'process-instances'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'process-class-instances', processClass] })
      return result
    },
  })

  return {
    updateProcessInstance: updateProcessInstanceMutation,
    isUpdating,
  }
})
