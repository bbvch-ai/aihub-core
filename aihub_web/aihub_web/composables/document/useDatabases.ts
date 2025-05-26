import { type DatabaseDto, getDatabases } from '@core/sdk/client'

export const useDatabases = defineQuery(() => {
  const { data: databases, isPending: databasesAreLoading } = useQuery<DatabaseDto[]>({
    key: () => ['knowledge'],
    staleTime: 1000 * 60 * 5, // 5 minutes
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
