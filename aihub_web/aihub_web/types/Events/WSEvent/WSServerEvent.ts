import type { EventData } from '@core/types/Event'
import type { AgentTopic } from '@core/types/topic/AgentTopic'

export interface WSServerEvent extends AgentTopic {
  event_data: EventData
}
