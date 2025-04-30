import { getThread, type ThreadDto } from '@core/sdk/client'

export default defineQuery(() => {
  const route = useRoute()
  return useQuery<ThreadDto>({
    key: () => ['thread', route.params.thread_id],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: async () => {
      return await getThread({
        composable: '$fetch',
        path: {
          thread_id: route.params.thread_id,
        },
      })
    },
  })
})
