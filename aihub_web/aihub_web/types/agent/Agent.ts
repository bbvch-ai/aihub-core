import type { AgentConfig } from '@core/types/agent/AgentConfig'
import type { EventSpecs } from '@core/types/Events/start_event/EventSpecs'

export interface Agent {
  agent_class: string
  agent_id: string
  agent_config: AgentConfig
  start_events: EventSpecs[]
  stop_events: EventSpecs[]
}
