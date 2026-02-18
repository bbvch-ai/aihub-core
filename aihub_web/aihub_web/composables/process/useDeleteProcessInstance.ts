import { deleteProcessInstance } from '@core/sdk/client'

export const useDeleteProcessInstance = defineMutation(() => {
  const queryCache = useQueryCache()

  const {
    mutateAsync: deleteProcessInstanceMutation,
    isPending: isDeleting,
    error: deleteError,
  } = useMutation({
    mutation: async ({ processClass, processId }: { processClass: string, processId: string }) => {
      await deleteProcessInstance({
        composable: '$fetch',
        path: {
          process_class: processClass,
          process_id: processId,
        },
      })

      queryCache.invalidateQueries({ key: ['process-instances'] })
      queryCache.invalidateQueries({ key: ['process-class-instances', processClass] })
    },
  })

  return {
    deleteProcessInstance: deleteProcessInstanceMutation,
    isDeleting,
    deleteError,
  }
})
