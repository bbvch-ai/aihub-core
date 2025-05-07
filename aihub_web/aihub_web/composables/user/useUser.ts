import { getMyUser, type MyUserDto } from '@core/sdk/client'

export default defineQuery(() => {
  const {
    data: user,
    status: loadingUser,
    refresh: refreshUser,
    refetch: refetchUser,
  } = useQuery<MyUserDto>({
    key: () => ['my_user'],
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
