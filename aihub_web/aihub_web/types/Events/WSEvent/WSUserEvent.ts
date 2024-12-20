import type { UserMessageEvent } from '@core/types/Events/UserEvents/UserMessageEvent'
import type { HumanInTheLoopResponseEvent } from '@core/types/Events/HumanInTheLoopEvents/HumanInTheLoopResponseEvent'

export interface WSUserEvent {
  thread_id: string
  display_id: string
  event: UserMessageEvent | HumanInTheLoopResponseEvent
}
