import { getMyAccount, type UserWithAccessDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const {
    data: myUser,
    isPending: myUserIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['my_user', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getMyAccount({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })
  return {
    myUser,
    myUserIsLoading,
  }
})
