import { getMyActiveTenant, setMyActiveTenant } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useActiveTenantQuery = defineQuery(() => {
  const { data: activeTenant, isPending: activeTenantIsLoading } = useQuery({
    key: () => ['active-tenant'],
    staleTime: minutesToMilliseconds(1),
    query: async () => await getMyActiveTenant({ composable: '$fetch' }),
  })
  return { activeTenant, activeTenantIsLoading }
})

export const useSetActiveTenant = defineMutation(() => {
  const queryCache = useQueryCache()
  const { mutateAsync: setActiveTenantMutation } = useMutation({
    mutation: async ({ tenantId }: { tenantId: string }) => {
      const result = await setMyActiveTenant({
        composable: '$fetch',
        body: { tenant_id: tenantId },
      })
      queryCache.invalidateQueries({ key: ['active-tenant'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
      return result
    },
  })
  return { setActiveTenant: setActiveTenantMutation }
})
