import { useWebSocket } from '@vueuse/core'
import { defineStore } from 'pinia'

import type { WsServerEvent } from '@core/sdk/client'

export const useEventsStore = defineStore('events', () => {
  const { getBearer } = useAuth()

  const newEvents = ref<WsServerEvent[]>([])

  const {
    data: newEvent,
    send,
    status: webSocketsStatus,
  } = useWebSocket<string>(`ws://localhost:8000/api/v1/event/ws`, {
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

  // Generic send event function
  const sendEvent = (event: WsServerEvent) => {
    send(JSON.stringify(event))
  }

  watch(
    () => newEvent.value,
    (receivedEvent) => {
      if (receivedEvent) {
        const event = JSON.parse(receivedEvent) as WsServerEvent
        newEvents.value.push(event)
      }
    },
  )

  // Combine, deduplicate, and sort events by creation date
  const events = computed<WsServerEvent[]>(() => {
    const allEvents = [...newEvents.value]

    // Remove duplicates based on event_id
    const uniqueEventsMap = new Map<string, WsServerEvent>()
    allEvents.forEach((event) => {
      uniqueEventsMap.set(event.event.event_id, event)
    })
    const uniqueEvents = Array.from(uniqueEventsMap.values())
    // Sort events by creation date
    return uniqueEvents.sort(
      (a, b) => a.event.created_at - b.event.created_at,
    )
  })

  const eventsForThread = (thread_id: string, display_id?: string) => {
    return computed<WsServerEvent>(() => {
      return events.value.filter((event) => {
        return event.thread_id === thread_id
          && (!display_id || event.display_id === display_id)
      })
    })
  }

  return {
    webSocketsStatus,
    events,
    eventsForThread,
    sendEvent,
  }
})
