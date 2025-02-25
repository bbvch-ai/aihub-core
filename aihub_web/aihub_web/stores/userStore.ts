import { getUser, type GetUserResponse } from '@core/sdk/client'

export const useUserStore = defineStore('user', () => {
  const {
    data: user,
    state: loadingUser,
    refresh: refreshUser,
    refetch: refetchUser,
  } = useQuery<GetUserResponse>({
    key: ['user'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getUser({
        composable: '$fetch',
      })
    },
  })

  return {
    user,
    loadingUser,
    refreshUser,
    refetchUser,
  }
})
