import { defineStore } from 'pinia'
import { useQuery } from '@pinia/colada'
import { useWebSocket } from '@vueuse/core'
import ObjectID from 'bson-objectid'
import type { WSUserEvent } from '@core/types/Events/WSEvent/WSUserEvent'
import type { HumanInTheLoopResponseEvent } from '@core/types/Events/HumanInTheLoopEvents/HumanInTheLoopResponseEvent'
import type { UserMessageEvent } from '@core/types/Events/UserEvents/UserMessageEvent'
import type { WSServerEvent } from '@core/types/Events/WSEvent/WSServerEvent'

export const useEventsStore = defineStore('events', () => {
  const { getHeaders, getBearer } = useAuth()

  const newEvents = ref<WSServerEvent[]>([])

  const {
    data: oldEvents,
    state: initialRequestState,
    refresh: refreshEvents,
    refetch: refetchEvents,
  } = useQuery<WSServerEvent[]>({
    key: ['events'],
    query: () =>
      getHeaders()
        .then(headers => fetch(`/api/v1/event/`, { headers: headers }))
        .then(res => res.json()),
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
  const sendEvent = (event: WSUserEvent) => {
    console.log('Sending', event)
    send(JSON.stringify(event))
  }

  watch(
    () => newEvent.value,
    (receivedEvent) => {
      console.log('Received data', receivedEvent)
      if (receivedEvent) {
        const event = JSON.parse(receivedEvent) as WSServerEvent
        console.log('Pushing new event')
        newEvents.value.push(event)
      }
    },
  )

  // Combine, deduplicate, and sort events by creation date
  const events = computed<WSServerEvent[]>(() => {
    const allEvents = [...newEvents.value]
    if (oldEvents.value) {
      allEvents.push(...oldEvents.value)
    }
    // Remove duplicates based on event_id
    const uniqueEventsMap = new Map<string, WSServerEvent>()
    allEvents.forEach((event) => {
      uniqueEventsMap.set(event.event_data.event_id, event)
    })
    const uniqueEvents = Array.from(uniqueEventsMap.values())
    // Sort events by creation date
    return uniqueEvents.sort(
      (a, b) => a.event_data.created_at - b.event_data.created_at,
    )
  })

  const sendUserMessageEvent = (thread_id: string, content: string, display_id?: string) => {
    const userMessageEvent: WSUserEvent = {
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
        && event.event_data._type === 'HumanInTheLoopRequestEvent'
      )
    })
    if (lastHumanInTheLoopRequestEvent) {
      console.log('Found last HumanInTheLoopRequestEvent', lastHumanInTheLoopRequestEvent)
      const humanInTheLoopResponseEvent: WSUserEvent = {
        thread_id,
        display_id: lastHumanInTheLoopRequestEvent.display_id,
        event: {
          _type: 'HumanInTheLoopResponseEvent',
          event_id: (ObjectID()).toHexString(),
          created_at: Date.now() * 1_000_000,
          response: content,
          request_event: lastHumanInTheLoopRequestEvent.event_data,
        } as HumanInTheLoopResponseEvent,
      }
      sendEvent(humanInTheLoopResponseEvent)
    }
    else {
      console.warn('No HumanInTheLoopRequestEvent found for thread_id', thread_id)
    }
  }

  return {
    initialRequestState,
    refreshEvents,
    refetchEvents,
    webSocketsStatus,
    events,
    sendUserMessageEvent,
    sendHumanInTheLoopResponse,
    sendEvent,
  }
})
