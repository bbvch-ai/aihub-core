import { getThread, type ThreadDto } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useThread = defineQuery(() => {
  const route = useRoute()
  const { data: thread, isLoading: threadIsLoading } = useQuery<ThreadDto>({
    key: () => ['threads', route.params.thread_id as string],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: async () => {
      return await getThread({
        composable: '$fetch',
        path: {
          thread_id: route.params.thread_id as string,
        },
      })
    },
  })
  return {
    thread,
    threadIsLoading,
  }
})
