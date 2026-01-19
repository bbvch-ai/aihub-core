import { getMyAccount, type UserWithAccessDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const {
    data: myUser,
    isPending: myUserIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['my_account'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getMyAccount({
        composable: '$fetch',
      })
    },
  })
  return {
    myUser,
    myUserIsLoading,
  }
})
