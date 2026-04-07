import { getRole, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()
  const isRouteReady = useRouteReady('role_id')

  const {
    data: role,
    isPending: roleIsLoading,
  } = useQuery<RoleResponse>({
    key: () => ['roles', tenantId.value, route.params.role_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantId.value),
    query: async () => {
      return await getRole({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          role_id: route.params.role_id as string,
        },
      })
    },
  })
  return {
    role,
    roleIsLoading,
  }
})
