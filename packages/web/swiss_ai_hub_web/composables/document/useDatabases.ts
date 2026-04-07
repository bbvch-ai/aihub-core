import { type DatabaseDto, getDatabases } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useDatabases = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const { data: databases, isPending: databasesAreLoading } = useQuery<DatabaseDto[]>({
    key: () => ['knowledge', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getDatabases({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })

  return {
    databases,
    databasesAreLoading,
  }
})
