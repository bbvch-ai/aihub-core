import { createRole, type CreateRoleRequest } from '@core/sdk/client'

export const useCreateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: createRoleMutation } = useMutation({
    mutation: async ({ createdRole, tenantId }: { createdRole: CreateRoleRequest, tenantId: string }) => {
      await createRole({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: createdRole,
      })
      queryCache.invalidateQueries()
    },
  })
  return {
    createRole: createRoleMutation,
  }
})
