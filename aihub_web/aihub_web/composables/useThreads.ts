import { getUserThreads, type ThreadDto } from '@core/sdk/client'

export default defineQuery(() => {
  return useQuery<ThreadDto[]>({
    key: () => ['threads'],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: async () => {
      return await getUserThreads({
        composable: '$fetch',
      })
    },
  })
})
