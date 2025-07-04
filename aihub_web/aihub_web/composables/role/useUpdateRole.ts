import { updateRole, type UpdateRoleRequest } from '@core/sdk/client'

export const useUpdateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutate: updateRoleMutation } = useMutation({
    mutation: async ({ roleId, updatedRole }: { roleId: string, updatedRole: UpdateRoleRequest }) => {
      await updateRole({
        composable: '$fetch',
        path: {
          role_id: roleId,
        },
        body: updatedRole,
      })
      queryCache.invalidateQueries({ key: ['roles'] })
    },
  })
  return {
    updateRole: updateRoleMutation,
  }
})
