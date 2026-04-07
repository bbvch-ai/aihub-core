import { getRoles, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantId } = useTenant()

  const {
    data: roles,
    isPending: rolesAreLoading,
  } = useQuery<RoleResponse[]>({
    key: () => ['roles', tenantId.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantId.value),
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
