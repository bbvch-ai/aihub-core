import { getUser, type UserWithAccessDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()

  const {
    data: user,
    isPending: userIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['users', route.params.user_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getUser({
        composable: '$fetch',
        path: {
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
