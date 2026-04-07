import { getRoles, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const {
    data: roles,
    isPending: rolesAreLoading,
  } = useQuery<RoleResponse[]>({
    key: () => ['roles', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getRoles({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })
  return {
    roles,
    rolesAreLoading,
  }
})
