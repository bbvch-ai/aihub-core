import { type DatabaseDto, getDatabases } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useDatabases = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: databases, isPending: databasesAreLoading } = useQuery<DatabaseDto[]>({
    key: () => ['knowledge', tenantId.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantId.value),
    query: async () => {
      return await getDatabases({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    databases,
    databasesAreLoading,
  }
})
