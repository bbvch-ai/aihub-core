import { getRole, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('role_id')

  const {
    data: role,
    isPending: roleIsLoading,
  } = useQuery<RoleResponse>({
    key: () => ['roles', route.params.role_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await getRole({
        composable: '$fetch',
        path: {
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
