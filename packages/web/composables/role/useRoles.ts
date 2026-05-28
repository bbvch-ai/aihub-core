import { getRoles, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantId } = useTenant()

  const {
    data: roles,
    isPending: rolesAreLoading,
  } = useQuery<RoleResponse[]>({
    key: () => ['tenant', tenantId.value, 'roles'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getRoles({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })
  return {
    roles,
    rolesAreLoading,
  }
})
