import { computed } from 'vue'
import { useEventsStore } from '@core/stores/useEventsStore'
import type { WSServerEvent } from '@core/types/Events/WSEvent/WSServerEvent'

export const useThread = (thread_id: string) => {
  const eventsStore = useEventsStore()

  const events = computed<WSServerEvent[]>(() => {
    return eventsStore.events.filter(
      event => event.thread_id === thread_id,
    )
  })

  const sendUserMessageEvent = (content: string, display_id?: string) => {
    eventsStore.sendUserMessageEvent(thread_id, content, display_id)
  }

  const sendHumanInTheLoopResponse = (content: string) => {
    eventsStore.sendHumanInTheLoopResponse(thread_id, content)
  }

  return {
    ...eventsStore,
    events,
    sendUserMessageEvent,
    sendHumanInTheLoopResponse,
  }
}
