import { computed } from 'vue'
import { useEventsStore } from '@core/stores/useEventsStore'
import type { WSServerEvent } from '@core/types/Events/WSEvent/WSServerEvent'
import { useThreadStore } from '@core/stores/useThreadStore'

export const useThread = (thread_id: string) => {
  const eventsStore = useEventsStore()
  const threadStore = useThreadStore()

  const details = threadStore.threadMap[thread_id]

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
    details,
    events,
    sendUserMessageEvent,
    sendHumanInTheLoopResponse,
  }
}
