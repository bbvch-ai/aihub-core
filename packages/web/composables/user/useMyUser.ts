import { getMyAccount, type UserWithAccessDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantId } = useTenant()

  const {
    data: myUser,
    isPending: myUserIsLoading,
  } = useQuery<UserWithAccessDto>({
    key: () => ['tenant', tenantId.value, 'my_user'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getMyAccount({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })
  return {
    myUser,
    myUserIsLoading,
  }
})
