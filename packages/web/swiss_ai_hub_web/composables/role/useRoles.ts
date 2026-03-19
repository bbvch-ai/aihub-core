import { getRoles, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const {
    data: roles,
    isPending: rolesAreLoading,
  } = useQuery<RoleResponse[]>({
    key: () => ['roles'],
    staleTime: minutesToMilliseconds(5),
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
