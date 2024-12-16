import type { BaseEvent, EventData } from '@core/types/Event'

export interface HumanInTheLoopResponseEvent extends BaseEvent {
  response: string
  request_event: EventData
}
