import type { BaseEvent } from '@core/types/Event'
import type { AgentTopic } from '@core/types/topic/AgentTopic'

export interface HumanInTheLoopRequestEvent extends BaseEvent {
  question: string
  topic: AgentTopic
}
