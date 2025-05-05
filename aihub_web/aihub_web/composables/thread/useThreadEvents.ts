import { getEvents, type WsServerEvent } from '@core/sdk/client'
import { useQuery, useQueryCache } from '@pinia/colada'
import { useWebSocket } from '@vueuse/core'
import { useRoute } from 'vue-router'

export const useThreadEvents = defineQuery(() => {
  const { getBearer } = useAuth()

  const route = useRoute()
  const queryCache = useQueryCache()

  // Regular REST API query
  const { data: threadEvents, isLoading: threadEventsAreLoading } = useQuery<WsServerEvent[]>({
    key: () => ['events', 'thread', route.params.thread_id as string],
    staleTime: 1000 * 10, // 10 seconds
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

  const { data: newEvent } = useWebSocket<string>('ws://localhost:8000/api/v1/event/ws', {
    autoReconnect: {
      retries: -1,
      delay: 1000,
    },
    onConnected(ws) {
      getBearer()
        .then((token) => {
          ws.send(JSON.stringify({ type: 'auth', token }))
        })
    },
  })

  // Update cache when new events arrive via WebSocket
  watch(() => newEvent.value, (rawEventData) => {
    if (!rawEventData) return

    try {
      const event = JSON.parse(rawEventData) as WsServerEvent

      // Only process events for the current thread
      if (event.thread_id === route.params.thread_id) {
        // Get current events from cache
        const currentEvents = queryCache.getQueryData<WsServerEvent[]>(['events', 'thread', route.params.thread_id]) || []

        // Check if event already exists (avoid duplicates)
        const eventExists = currentEvents.some(e => e.event_id === event.event_id)

        if (!eventExists) {
          // Add new event to the cache
          const updatedEvents = [...currentEvents, event]

          // Sort events if needed
          updatedEvents.sort((a, b) =>
            (a.event.created_at ?? 0) - (b.event.created_at ?? 0),
          )

          // Update the cache with the new array
          queryCache.setQueryData(['events', 'thread', route.params.thread_id], updatedEvents)
        }
      }
    }
    catch (error) {
      console.error('Error processing WebSocket event:', error)
    }
  })

  return {
    threadEvents,
    threadEventsAreLoading,
  }
})
