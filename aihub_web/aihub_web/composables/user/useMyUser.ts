import { getMyUser, type UserDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const {
    data: myUser,
    isPending: myUserIsLoading,
  } = useQuery<UserDto>({
    key: () => ['my_user'],
    staleTime: minutesToMilliseconds(5),
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
