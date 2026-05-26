import { assignRole } from '@core/sdk/client'

export const useAssignRoleToUser = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync, isLoading } = useMutation({
    mutation: async ({ tenantId, userId, roleName }: { tenantId: string, userId: string, roleName: string }) => {
      const result = await assignRole({
        composable: '$fetch',
        path: { tenant_id: tenantId, user_id: userId },
        body: { role_name: roleName },
      })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'users'] })
      return result
    },
  })

  return {
    assignRole: mutateAsync,
    assignRoleIsLoading: isLoading,
  }
})
