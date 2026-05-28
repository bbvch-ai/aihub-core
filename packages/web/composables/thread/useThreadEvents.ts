import { getAgentEventsInThread, type ContextualizedAgentEvent } from '@core/sdk/client'
import { useWebSocket } from '@vueuse/core'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useThreadEvents = defineQuery(() => {
  const { getBearer } = useAuth()
  const runtimeConfig = useRuntimeConfig()

  const route = useRoute()
  const { tenantId } = useTenant()
  const queryCache = useQueryCache()

  const { data: threadEvents, isPending: threadEventsAreLoading } = useQuery<ContextualizedAgentEvent[]>({
    key: () => ['tenant', tenantId.value, 'thread', route.params.thread_id as string, 'events'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('thread_id'),
    query: async () => {
      return await getAgentEventsInThread({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          thread_id: route.params.thread_id as string,
        },
      })
    },
  })

  const { data: newEvent } = useWebSocket<string>(runtimeConfig.public.ws.endpoint, {
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
      const event = JSON.parse(rawEventData) as ContextualizedAgentEvent

      // Only process events for the current thread
      if (event.thread_id === route.params.thread_id) {
        // Get current events from cache
        const key = ['tenant', tenantId.value, 'thread', route.params.thread_id, 'events']
        const currentEvents = queryCache.getQueryData<ContextualizedAgentEvent[]>(key) || []

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
          queryCache.setQueryData(key, updatedEvents)
        }

        // Invalidate queries on stop event
        const parents = event.event._parent_event_names
        if (parents.includes('StopEvent') || parents.includes('ExceptionEvent')) {
          new Promise(r => setTimeout(r, 500)).then(() => {
            queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'threads'] })
            queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'threads', event.thread_id] })
            queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'agent', event.agent_class, event.agent_id] })
          })
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
