import { revokeRole } from '@core/sdk/client'

export const useRevokeRoleFromUser = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync, isLoading } = useMutation({
    mutation: async ({ tenantId, userId, roleName }: { tenantId: string, userId: string, roleName: string }) => {
      const result = await revokeRole({
        composable: '$fetch',
        path: { tenant_id: tenantId, user_id: userId, role_name: roleName },
      })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'users'] })
      return result
    },
  })

  return {
    revokeRole: mutateAsync,
    revokeRoleIsLoading: isLoading,
  }
})
