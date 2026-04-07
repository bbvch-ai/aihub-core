import { getUser, type UserWithAccessDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()
  const isRouteReady = useRouteReady('user_id')

  const {
    data: user,
    isPending: userIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['users', tenantId.value, route.params.user_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantId.value),
    query: async () => {
      return await getUser({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          user_id: route.params.user_id as string,
        },
      })
    },
  })
  return {
    user,
    userIsLoading,
  }
})
