import { getMyUser, type MyUserDto } from '@core/sdk/client'

export const useUserStore = defineStore('user', () => {
  const {
    data: user,
    status: loadingUser,
    refresh: refreshUser,
    refetch: refetchUser,
  } = useQuery<MyUserDto>({
    key: ['user'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getMyUser({
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
