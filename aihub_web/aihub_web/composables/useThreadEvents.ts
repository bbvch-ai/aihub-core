import { getEvents, type WsServerEvent } from '@core/sdk/client'

export default defineQuery(() => {
  const route = useRoute()
  return useQuery<WsServerEvent[]>({
    key: () => ['events', 'thread', route.params.thread_id],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: async () => {
      return await getEvents({
        composable: '$fetch',
        query: {
          thread_id: route.params.thread_id,
        },
      })
    },
  })
})
