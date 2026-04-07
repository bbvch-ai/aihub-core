import { updateRole, type UpdateRoleRequest } from '@core/sdk/client'

export const useUpdateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateRoleMutation } = useMutation({
    mutation: async ({ roleId, updatedRole, tenantId }: { roleId: string, updatedRole: UpdateRoleRequest, tenantId: string }) => {
      await updateRole({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
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
