import { getRole, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const {
    data: role,
    isPending: roleIsLoading,
  } = useQuery<RoleResponse>({
    key: () => ['tenant', tenantId.value, 'roles', route.params.role_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('role_id'),
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
