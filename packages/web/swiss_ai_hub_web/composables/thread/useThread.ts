import { getThread, type ThreadDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useThread = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('thread_id')

  const { data: thread, isPending: threadIsLoading } = useQuery<ThreadDto>({
    key: () => ['threads', route.params.thread_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
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
