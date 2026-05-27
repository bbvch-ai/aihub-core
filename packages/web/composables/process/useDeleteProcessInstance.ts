import { deleteProcessInstance } from '@core/sdk/client'

export const useDeleteProcessInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteProcessInstanceMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ processClass, processId, tenantId }: { processClass: string, processId: string, tenantId: string }) => {
      await deleteProcessInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          process_class: processClass,
          process_id: processId,
        },
      })

      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'process-instances'] })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'process-class-instances', processClass] })
    },
  })

  return {
    deleteProcessInstance: deleteProcessInstanceMutation,
    isDeleting,
    deleteError,
  }
})
