import { getRoles, type RoleResponse } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const {
    data: roles,
    isPending: rolesAreLoading,
  } = useQuery<RoleResponse>({
    key: () => ['roles'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getRoles({
        composable: '$fetch',
      })
    },
  })
  return {
    roles,
    rolesAreLoading,
  }
})
