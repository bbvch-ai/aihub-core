import { type DatabaseDto, getDatabases } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useDatabases = defineQuery(() => {
  const { data: databases, isPending: databasesAreLoading } = useQuery<DatabaseDto[]>({
    key: () => ['knowledge'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getDatabases({
        composable: '$fetch',
      })
    },
  })

  return {
    databases,
    databasesAreLoading,
  }
})
