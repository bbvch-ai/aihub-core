import { getEvents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { useWebSocket } from '@vueuse/core'
import ObjectID from 'bson-objectid'
import { defineStore } from 'pinia'

import type { WsServerEvent, UserMessageEvent } from '@core/sdk/client'

export const useEventsStore = defineStore('events', () => {
  const { getBearer } = useAuth()

  const newEvents = ref<WsServerEvent[]>([])

  const {
    data: oldEvents,
    state: initialRequestState,
    refresh: refreshEvents,
    refetch: refetchEvents,
  } = useQuery<WsServerEvent[]>({
    key: ['events'],
    query: () => getEvents({
      composable: '$fetch',
    }),
  })

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
    if (oldEvents.value) {
      allEvents.push(...oldEvents.value)
    }
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

  const sendUserMessageEvent = (thread_id: string, content: string, display_id?: string) => {
    const userMessageEvent: WsServerEvent = {
      thread_id,
      display_id: display_id || (ObjectID()).toHexString(),
      event: {
        _type: 'UserMessageEvent',
        event_id: (ObjectID()).toHexString(),
        created_at: Date.now() * 1_000_000,
        messages: [
          {
            role: 'user',
            content,
          },
        ],
      } as UserMessageEvent,
    }
    sendEvent(userMessageEvent)
  }

  const sendHumanInTheLoopResponse = (thread_id: string, content: string) => {
    const lastHumanInTheLoopRequestEvent = events.value.findLast((event) => {
      return (
        event.thread_id === thread_id
        && event.event._type === 'HumanInTheLoopRequestEvent'
      )
    })
    if (lastHumanInTheLoopRequestEvent) {
      const humanInTheLoopResponseEvent = {
        thread_id,
        display_id: lastHumanInTheLoopRequestEvent.display_id,
        event: {
          _type: 'HumanInTheLoopResponseEvent',
          event_id: (ObjectID()).toHexString(),
          created_at: Date.now() * 1_000_000,
          response: content,
          request_event: lastHumanInTheLoopRequestEvent.event,
        },
      }
      sendEvent(humanInTheLoopResponseEvent)
    }
    else {
      console.warn('No HumanInTheLoopRequestEvent found for thread_id', thread_id)
    }
  }

  const eventsForThread = (thread_id: string, display_id?: string) => {
    return computed<WsServerEvent>(() => {
      return events.value.filter((event) => {
        return event.thread_id === thread_id
          && (!display_id || event.display_id === display_id)
      })
    })
  }

  return {
    initialRequestState,
    refreshEvents,
    refetchEvents,
    webSocketsStatus,
    events,
    eventsForThread,
    sendUserMessageEvent,
    sendHumanInTheLoopResponse,
    sendEvent,
  }
})
