import { getRole, type RoleResponse } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()

  const {
    data: role,
    isPending: roleIsLoading,
  } = useQuery<RoleResponse>({
    key: () => ['roles', route.params.role_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
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
