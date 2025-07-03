import { getUser, type UserWithAccessDto } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()

  const {
    data: user,
    isPending: userIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['users', route.params.user_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
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
