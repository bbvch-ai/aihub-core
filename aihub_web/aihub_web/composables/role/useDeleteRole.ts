import { deleteRole } from '@core/sdk/client'

export const useDeleteRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutate: removeRole } = useMutation({
    mutation: async ({ roleId }: { roleId: string }) => {
      await deleteRole({
        composable: '$fetch',
        path: {
          role_id: roleId,
        },
      }),
      queryCache.invalidateQueries({ key: ['roles'] })
    },
  })
  return {
    deleteRole: removeRole,
  }
})
