import { updateRole, type UpdateRoleRequest } from '@core/sdk/client'

export const useUpdateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateRoleMutation } = useMutation({
    mutation: async ({ roleId, updatedRole }: { roleId: string, updatedRole: UpdateRoleRequest }) => {
      await updateRole({
        composable: '$fetch',
        path: {
          role_id: roleId,
        },
        body: updatedRole,
      })
      queryCache.invalidateQueries({ key: ['roles'] })
      queryCache.invalidateQueries({ key: ['suite'] })
    },
  })
  return {
    updateRole: updateRoleMutation,
  }
})
