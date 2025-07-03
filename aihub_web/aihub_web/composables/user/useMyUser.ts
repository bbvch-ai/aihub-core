import { getMyUser, type UserDto } from '@core/sdk/client'

export default defineQuery(() => {
  const {
    data: myUser,
    isPending: myUserIsLoading,
  } = useQuery<UserDto>({
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
    myUser,
    myUserIsLoading,
  }
})
